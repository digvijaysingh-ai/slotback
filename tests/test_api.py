"""HTTP layer: tool auth, token binding, signed webhooks, verify upload, kill switch."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo
from slotledger import sign_head, write_bundle
from slotledger.pg import load_events, load_snapshots
from slotledger.sign import new_private_key_hex

from slotback.api.app import Settings, create_app, verify_signature
from slotback.data.generate import generate_day
from slotback.data.seed import load_dataset
from slotback.db import apply_schema
from slotback.services import scheduling as svc

NOW = datetime(2026, 10, 14, 10, 0)
SECRET, HOOK, CODE = "tool-secret", "hook-secret", "letmein"


@pytest.fixture
def env(pg_url):
    schema = f"t_{uuid.uuid4().hex[:12]}"
    url = make_conninfo(pg_url, options=f"-csearch_path={schema}")
    with psycopg.connect(pg_url, autocommit=True) as c:
        c.execute(f'CREATE SCHEMA "{schema}"')
    conn = psycopg.connect(url, autocommit=True)
    apply_schema(conn)
    load_dataset(conn, generate_day(), "live")
    settings = Settings(url, SECRET, HOOK, CODE, "live", clock=lambda: NOW)
    with TestClient(create_app(settings)) as client:
        yield client, conn
    conn.close()
    with psycopg.connect(pg_url, autocommit=True) as c:
        c.execute(f'DROP SCHEMA "{schema}" CASCADE')


def creds(conn, pid):
    dob, idn = conn.execute(
        "SELECT date_of_birth, id_number FROM patients WHERE hospital_id = 'live' AND pid = %s",
        (pid,),
    ).fetchone()
    return {"date_of_birth": dob.isoformat(), "id_last3": idn[5:8], "id_letter": idn[-1]}


def tool(client, name, token, body=None, secret=SECRET):
    return client.post(
        f"/tools/{name}", json=body or {}, headers={"X-Tool-Secret": secret, "X-Call-Token": token}
    )


def test_tools_reject_missing_or_wrong_secret(env):
    client, _ = env
    assert tool(client, "get_appointment", "x", secret="nope").status_code == 401
    assert client.post("/tools/get_appointment", json={}).status_code == 401


def test_unknown_token_is_unauthorized_not_a_crash(env):
    client, _ = env
    r = tool(client, "get_appointment", "not-a-token")
    assert r.status_code == 200 and r.json()["error"] == "unauthorized"


def test_widget_session_binds_on_verify_and_never_takes_a_pid(env):
    client, conn = env
    assert client.post("/api/sessions", json={"access_code": "wrong"}).status_code == 403
    token = client.post("/api/sessions", json={"access_code": CODE}).json()["call_token"]
    r = tool(client, "get_appointment", token)
    assert r.json()["error"] == "identity_not_verified"
    pid = conn.execute(
        "SELECT pid FROM appointments WHERE hospital_id = 'live' ORDER BY appointment_id LIMIT 1"
    ).fetchone()[0]
    # A jailbroken agent adding a pid to the body changes nothing: the model has no pid field.
    r = tool(client, "verify_identity", token, {**creds(conn, pid), "pid": "P-00999"})
    assert r.json()["status"] == "verified"
    assert svc.resolve(conn, token).pid == pid
    assert tool(client, "get_appointment", token).json()["ok"] is True


def test_demo_call_session_is_bound_and_still_needs_identity(env):
    client, conn = env
    assert (
        client.post("/api/sessions", json={"access_code": CODE, "purpose": "backfill"}).status_code
        == 400
    )
    s = client.post("/api/sessions", json={"access_code": CODE, "purpose": "confirm"}).json()
    pid = conn.execute(
        "SELECT pid FROM appointments WHERE hospital_id = 'live' ORDER BY appointment_id LIMIT 1"
    ).fetchone()[0]
    assert svc.resolve(conn, s["call_token"]).pid == pid
    assert (
        tool(client, "get_appointment", s["call_token"]).json()["error"] == "identity_not_verified"
    )
    r = tool(client, "verify_identity", s["call_token"], creds(conn, pid)).json()
    # The agent learns it is a confirm call, so it never treats it as a backfill offer.
    assert (r["status"], r["call_purpose"]) == ("verified", "confirm")
    r = tool(client, "transfer_to_human", s["call_token"], {"reason": "patient asked"}).json()
    assert r["status"] == "callback_requested"  # no live transfer: never claim one


def test_bad_input_returns_422_the_agent_can_read(env):
    client, _ = env
    r = tool(
        client,
        "verify_identity",
        "t",
        {"date_of_birth": "yesterday", "id_last3": "12", "id_letter": "7"},
    )
    assert r.status_code == 422


def _signed(body: dict, secret=HOOK, t=None):
    raw = json.dumps(body).encode()
    t = t or int(time.time())
    sig = hmac.new(secret.encode(), f"{t}.".encode() + raw, hashlib.sha256).hexdigest()
    return raw, f"t={t},v0={sig}"


def test_post_call_webhook_needs_a_valid_signature(env):
    client, conn = env
    body = {
        "type": "call_initiation_failure",
        "data": {
            "failure_reason": "no-answer",
            "conversation_initiation_client_data": {"dynamic_variables": {"call_id": "x"}},
        },
    }
    raw, _ = _signed(body)
    r = client.post(
        "/hooks/post-call", content=raw, headers={"ElevenLabs-Signature": "t=1,v0=deadbeef"}
    )
    assert r.status_code == 401
    _, stale = _signed(body, t=int(time.time()) - 3600)
    assert (
        client.post(
            "/hooks/post-call", content=raw, headers={"ElevenLabs-Signature": stale}
        ).status_code
        == 401
    )


def test_no_answer_webhook_advances_the_backfill(env):
    client, conn = env
    pid = conn.execute(
        "SELECT pid FROM appointments WHERE hospital_id = 'live'"
        " AND specialty = 'cardiology' ORDER BY appointment_id LIMIT 1"
    ).fetchone()[0]
    _, t = svc.start_call(conn, "live", "confirm", NOW, pid=pid)
    svc.verify_identity(conn, t, *creds(conn, pid).values(), now=NOW)
    svc.cancel_appointment(conn, t, True, NOW)
    slot = conn.execute("SELECT slot_id FROM backfills").fetchone()[0]
    first = svc.next_backfill_target(conn, "live", slot, NOW)
    call_id, _ = svc.start_call(conn, "live", "backfill", NOW, pid=first["pid"], slot_id=slot)
    body = {
        "type": "call_initiation_failure",
        "data": {
            "failure_reason": "no-answer",
            "conversation_initiation_client_data": {"dynamic_variables": {"call_id": call_id}},
        },
    }
    raw, sig = _signed(body)
    r = client.post("/hooks/post-call", content=raw, headers={"ElevenLabs-Signature": sig})
    assert r.json()["status"] == "recorded"
    assert svc.next_backfill_target(conn, "live", slot, NOW)["rank"] == 2


def test_verify_upload_pass_tamper_and_garbage(env):
    client, conn = env
    pid = conn.execute(
        "SELECT pid FROM appointments WHERE hospital_id = 'live' ORDER BY appointment_id LIMIT 1"
    ).fetchone()[0]
    _, t = svc.start_call(conn, "live", "confirm", NOW, pid=pid)
    svc.verify_identity(conn, t, *creds(conn, pid).values(), now=NOW)
    svc.cancel_appointment(conn, t, True, NOW)
    cid = svc.chain_id(conn, "live")
    events, snaps = load_events(conn, cid), load_snapshots(conn, cid)
    key = new_private_key_hex()
    head = sign_head(key, cid, events[-1].seq, events[-1].hash, NOW.isoformat())
    good = write_bundle(events, snaps, head)
    r = client.post("/api/verify", files={"file": ("b.zip", good)})
    assert r.json()["ok"] is True
    from dataclasses import replace

    events[1] = replace(events[1], payload={**events[1].payload, "reason": "edited"})
    r = client.post("/api/verify", files={"file": ("b.zip", write_bundle(events, snaps, head))})
    assert r.json()["ok"] is False and r.json()["checks"]["chain"]["seq"] == 2
    r = client.post("/api/verify", files={"file": ("x.zip", b"<html>")})
    assert r.status_code == 400


def test_kill_switch_stops_new_calls(env):
    client, conn = env
    assert client.post("/api/kill-switch", params={"access_code": CODE, "paused": True}).json()[
        "calling_paused"
    ]
    with pytest.raises(svc.CallingPaused):
        svc.start_call(conn, "live", "confirm", NOW, pid="P-00001")
    assert conn.execute("SELECT count(*) FROM staff_actions").fetchone()[0] == 1


def test_signature_helper_rejects_tampered_body():
    raw, sig = _signed({"a": 1})
    assert verify_signature(HOOK, sig, raw, time.time())
    assert not verify_signature(HOOK, sig, raw + b" ", time.time())


def test_spare_capacity_lets_a_verified_patient_move_the_appointment(env):
    from slotback.serve import add_spare_capacity

    client, conn = env
    clinic = conn.execute(
        "SELECT clinic_date FROM hospitals WHERE hospital_id = 'live'"
    ).fetchone()[0]
    specs = [
        r[0]
        for r in conn.execute("SELECT DISTINCT specialty FROM slots WHERE hospital_id = 'live'")
    ]
    add_spare_capacity(conn, "live", clinic.isoformat(), specs)
    s = client.post("/api/sessions", json={"access_code": CODE, "purpose": "confirm"}).json()
    pid = svc.resolve(conn, s["call_token"]).pid
    tool(client, "verify_identity", s["call_token"], creds(conn, pid))
    slots = tool(client, "list_alternative_slots", s["call_token"]).json()["slots"]
    assert len(slots) >= 3
    r = tool(client, "reschedule", s["call_token"], {"slot_id": slots[0]["slot_id"]}).json()
    assert r["ok"] is True
