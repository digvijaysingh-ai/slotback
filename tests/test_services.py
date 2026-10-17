"""Service layer on real Postgres: the safety rules, end to end, with a fake clock."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from voiceledger.pg import load_events, load_snapshots

from slotback.data.generate import generate_day
from slotback.data.seed import load_dataset
from slotback.ledger import verify
from slotback.services import scheduling as svc

H = "h"
NOW = datetime(2026, 10, 14, 10, 0)  # two days before the clinic day, before cut-offs


@pytest.fixture
def db(pg):
    load_dataset(pg, generate_day(), H)
    return pg


def creds(conn, pid):
    dob, id_number = conn.execute(
        "SELECT date_of_birth, id_number FROM patients WHERE hospital_id = %s AND pid = %s",
        (H, pid),
    ).fetchone()
    return dob.isoformat(), id_number[5:8], id_number[-1]


def booked_pid(conn, specialty="cardiology"):
    return conn.execute(
        "SELECT pid FROM appointments WHERE hospital_id = %s AND specialty = %s"
        " ORDER BY appointment_id LIMIT 1",
        (H, specialty),
    ).fetchone()[0]


def waitlist(conn, specialty="cardiology"):
    return [
        r[0]
        for r in conn.execute(
            "SELECT pid FROM waitlist_entries WHERE hospital_id = %s AND specialty = %s"
            " ORDER BY rank",
            (H, specialty),
        )
    ]


def verified_call(conn, pid, purpose="confirm", slot_id=None, now=NOW):
    _, token = svc.start_call(conn, H, purpose, now, pid=pid, slot_id=slot_id)
    assert svc.verify_identity(conn, token, *creds(conn, pid), now)["status"] == "verified"
    return token


def ledger_report(conn):
    cid = svc.chain_id(conn, H)
    return verify(load_events(conn, cid), load_snapshots(conn, cid))


def test_nothing_is_disclosed_before_identity(db):
    pid = booked_pid(db)
    _, token = svc.start_call(db, H, "confirm", NOW, pid=pid)
    with pytest.raises(svc.NotVerified):
        svc.get_appointment(db, token, NOW)
    dob, last3, letter = creds(db, pid)
    wrong = "000" if last3 != "000" else "111"
    assert svc.verify_identity(db, token, dob, wrong, letter, NOW)["status"] == "failed"
    with pytest.raises(svc.NotVerified):
        svc.get_appointment(db, token, NOW)
    assert svc.verify_identity(db, token, dob, last3, letter, NOW)["status"] == "verified"
    assert svc.get_appointment(db, token, NOW)["specialty"] == "cardiology"
    assert svc.confirm_appointment(db, token, NOW)["status"] == "confirmed"
    assert ledger_report(db).ok


def test_two_failures_end_the_call(db):
    pid = booked_pid(db)
    _, token = svc.start_call(db, H, "confirm", NOW, pid=pid)
    dob, _, letter = creds(db, pid)
    assert svc.verify_identity(db, token, dob, "999", letter, NOW)["status"] == "failed"
    assert svc.verify_identity(db, token, dob, "998", letter, NOW)["status"] == "end_call"


def test_three_failed_calls_lock_automated_identity_for_24h(db):
    pid = booked_pid(db)
    dob, last3, letter = creds(db, pid)
    for i in range(3):
        _, t = svc.start_call(db, H, "confirm", NOW + timedelta(minutes=i), pid=pid)
        svc.verify_identity(db, t, dob, "999", letter, NOW + timedelta(minutes=i))
    _, t = svc.start_call(db, H, "confirm", NOW + timedelta(hours=1), pid=pid)
    assert (
        svc.verify_identity(db, t, dob, last3, letter, NOW + timedelta(hours=1))["status"]
        == "locked"
    )
    _, t = svc.start_call(db, H, "confirm", NOW + timedelta(hours=25), pid=pid)
    assert (
        svc.verify_identity(db, t, dob, last3, letter, NOW + timedelta(hours=25))["status"]
        == "verified"
    )


def test_unbound_inbound_token_binds_only_on_verify(db):
    pid = booked_pid(db)
    _, token = svc.start_call(db, H, "inbound", NOW)
    with pytest.raises(svc.NotVerified):
        svc.get_appointment(db, token, NOW)
    assert svc.verify_identity(db, token, *creds(db, pid), NOW)["status"] == "verified"
    assert svc.resolve(db, token).pid == pid


def test_cancel_needs_explicit_yes_then_starts_backfill_in_list_order(db):
    token = verified_call(db, booked_pid(db))
    with pytest.raises(svc.NeedsConfirmation):
        svc.cancel_appointment(db, token, False, NOW)
    svc.cancel_appointment(db, token, True, NOW)
    slot = db.execute("SELECT slot_id FROM backfills WHERE hospital_id = %s", (H,)).fetchone()[0]
    target = svc.next_backfill_target(db, H, slot, NOW)
    assert target == {"pid": waitlist(db)[0], "rank": 1}
    assert ledger_report(db).ok


def _freed_slot(db):
    token = verified_call(db, booked_pid(db))
    svc.cancel_appointment(db, token, True, NOW)
    return db.execute("SELECT slot_id FROM backfills WHERE hospital_id = %s", (H,)).fetchone()[0]


def test_full_backfill_no_answer_then_accept(db):
    slot = _freed_slot(db)
    wl = waitlist(db)
    call1, _ = svc.start_call(db, H, "backfill", NOW, pid=wl[0], slot_id=slot)
    svc.record_call_outcome(db, call1, "no_answer", NOW + timedelta(minutes=1))
    assert svc.next_backfill_target(db, H, slot, NOW)["pid"] == wl[1]
    t2 = verified_call(db, wl[1], "backfill", slot, NOW + timedelta(minutes=2))
    offer = svc.offer_backfill(db, t2, NOW + timedelta(minutes=2))
    assert offer["hold_minutes"] == 10
    assert svc.accept_backfill(db, t2, NOW + timedelta(minutes=3))["status"] == "booked"
    assert (
        db.execute(
            "SELECT status FROM slots WHERE hospital_id = %s AND slot_id = %s", (H, slot)
        ).fetchone()[0]
        == "filled"
    )
    report = ledger_report(db)
    assert report.ok, report.to_dict()
    assert report.checks["list_order"].status == "pass"


def test_lower_rank_cannot_be_called_while_rank_one_is_open(db):
    slot = _freed_slot(db)
    with pytest.raises(svc.NotEligible):
        svc.start_call(db, H, "backfill", NOW, pid=waitlist(db)[1], slot_id=slot)


def test_hold_expiry_then_late_accept_is_rejected(db):
    slot = _freed_slot(db)
    wl = waitlist(db)
    t1 = verified_call(db, wl[0], "backfill", slot)
    svc.offer_backfill(db, t1, NOW)
    assert svc.sweep(db, H, NOW + timedelta(minutes=11))["expired"] == 1
    with pytest.raises(svc.SlotTaken):
        svc.accept_backfill(db, t1, NOW + timedelta(minutes=12))
    types = [e.type for e in load_events(db, svc.chain_id(db, H))]
    assert "late_accept_rejected" in types
    assert svc.next_backfill_target(db, H, slot, NOW + timedelta(minutes=12))["pid"] == wl[1]
    assert ledger_report(db).ok


def test_opted_out_patient_is_skipped_with_a_logged_reason(db):
    slot = _freed_slot(db)
    wl = waitlist(db)
    db.execute(
        "UPDATE patients SET opted_out = true WHERE hospital_id = %s AND pid = %s", (H, wl[0])
    )
    assert svc.next_backfill_target(db, H, slot, NOW)["pid"] == wl[1]
    types = [e.type for e in load_events(db, svc.chain_id(db, H))]
    assert "rank_skipped" in types
    assert ledger_report(db).ok


def test_duplicate_webhook_is_idempotent(db):
    slot = _freed_slot(db)
    call1, _ = svc.start_call(db, H, "backfill", NOW, pid=waitlist(db)[0], slot_id=slot)
    assert svc.record_call_outcome(db, call1, "voicemail", NOW)["status"] == "recorded"
    assert svc.record_call_outcome(db, call1, "voicemail", NOW)["status"] == "already_recorded"
    assert ledger_report(db).ok


def test_reschedule_is_an_atomic_swap(db):
    pid = booked_pid(db)
    open_slot = db.execute(
        "SELECT slot_id FROM slots WHERE hospital_id = %s AND specialty = 'cardiology'"
        " ORDER BY slot_id DESC LIMIT 1",
        (H,),
    ).fetchone()[0]
    db.execute(
        "UPDATE slots SET status = 'unfilled' WHERE hospital_id = %s AND slot_id = %s",
        (H, open_slot),
    )
    token = verified_call(db, pid)
    old = svc.get_appointment(db, token, NOW)
    alts = svc.list_alternative_slots(db, token, NOW)["slots"]
    assert open_slot in [s["slot_id"] for s in alts]
    svc.reschedule(db, token, open_slot, NOW)
    n = db.execute(
        "SELECT count(*) FROM appointments WHERE hospital_id = %s AND pid = %s"
        " AND status IN ('scheduled', 'confirmed')",
        (H, pid),
    ).fetchone()[0]
    assert n == 1
    assert svc.get_appointment(db, token, NOW)["starts_at"] != old["starts_at"]
    assert ledger_report(db).ok


def test_reschedule_to_a_taken_slot_changes_nothing(db):
    pid = booked_pid(db)
    token = verified_call(db, pid)
    before = svc.get_appointment(db, token, NOW)
    with pytest.raises(svc.SlotTaken):
        svc.reschedule(db, token, "S-CAR-1-0480", NOW)
    assert svc.get_appointment(db, token, NOW) == before


def test_kill_switch_and_campaign_dedupe(db):
    pid = booked_pid(db)
    svc.start_call(db, H, "confirm", NOW, pid=pid, campaign_key="A-1:2026-10-14")
    with pytest.raises(svc.AlreadyCalled):
        svc.start_call(db, H, "confirm", NOW, pid=pid, campaign_key="A-1:2026-10-14")
    db.execute("INSERT INTO settings (hospital_id, calling_paused) VALUES (%s, true)", (H,))
    with pytest.raises(svc.CallingPaused):
        svc.start_call(db, H, "confirm", NOW, pid=pid)


def test_showcase_hospital_is_read_only(pg):
    load_dataset(pg, generate_day(), "showcase", read_only=True)
    with pytest.raises(svc.ReadOnly):
        svc.start_call(pg, "showcase", "confirm", NOW, pid="P-00001")


def test_slots_are_never_freed_by_prediction(db):
    with pytest.raises(ValueError):
        svc.free_slot(db, H, "S-CAR-1-0480", "predicted_no_show", "system", NOW)
