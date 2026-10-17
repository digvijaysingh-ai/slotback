"""Deterministic tool-level scenarios, run through the real service layer.

Each runs on its own hospital (fresh synthetic day) so runs never touch the showcase or
each other (EOV5). Each returns {check_name: bool}; the ledger is verified every time.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from voiceledger.pg import load_events, load_snapshots

from slotback.api.models import VerifyIdentity
from slotback.data.generate import generate_day
from slotback.data.seed import load_dataset
from slotback.ledger import verify
from slotback.services import scheduling as svc

NOW = datetime(2026, 10, 14, 10, 0)


def _setup(conn, hospital):
    load_dataset(conn, generate_day(), hospital)


def _first_booked(conn, h, specialty="cardiology"):
    return conn.execute(
        "SELECT pid FROM appointments WHERE hospital_id = %s AND specialty = %s"
        " ORDER BY appointment_id LIMIT 1",
        (h, specialty),
    ).fetchone()[0]


def _creds(conn, h, pid):
    dob, idn = conn.execute(
        "SELECT date_of_birth, id_number FROM patients WHERE hospital_id = %s AND pid = %s",
        (h, pid),
    ).fetchone()
    return dob.isoformat(), idn[5:8], idn[-1]


def _wrong(last3):
    return "000" if last3 != "000" else "111"


def _types(conn, h, call_id=None):
    evs = load_events(conn, svc.chain_id(conn, h))
    return [e.type for e in evs if call_id is None or e.payload.get("call_id") == call_id]


def _ledger_ok(conn, h):
    cid = svc.chain_id(conn, h)
    return verify(load_events(conn, cid), load_snapshots(conn, cid)).ok


def _verified_call(conn, h, pid, purpose="confirm", slot=None, now=NOW):
    call_id, tok = svc.start_call(conn, h, purpose, now, pid=pid, slot_id=slot)
    svc.record_disclosure(conn, tok, now)
    svc.verify_identity(conn, tok, *_creds(conn, h, pid), now=now)
    return call_id, tok


def happy_confirm_es(conn, h):
    pid = _first_booked(conn, h)
    call_id, tok = _verified_call(conn, h, pid)
    svc.get_appointment(conn, tok, NOW)
    svc.confirm_appointment(conn, tok, NOW)
    t = _types(conn, h, call_id)
    return {
        "ai_disclosure_first": t[0] == "ai_disclosed",
        "read_back_before_confirm": t.index("read_back") < t.index("appointment_confirmed"),
        "ledger_verifies": _ledger_ok(conn, h),
    }


def relative_answers(conn, h):
    pid = _first_booked(conn, h)
    call_id, tok = svc.start_call(conn, h, "confirm", NOW, pid=pid)
    dob, last3, letter = _creds(conn, h, pid)
    r1 = svc.verify_identity(conn, tok, dob, _wrong(last3), letter, NOW)
    r2 = svc.verify_identity(conn, tok, "1990-01-01", _wrong(last3), letter, NOW)
    blocked = False
    try:
        svc.get_appointment(conn, tok, NOW)
    except svc.NotVerified:
        blocked = True
    return {
        "no_detail_without_identity": blocked,
        "call_ends_after_two_failures": r1["status"] == "failed" and r2["status"] == "end_call",
        "nothing_disclosed": "detail_disclosed" not in _types(conn, h, call_id),
    }


def social_engineering(conn, h):
    victim = _first_booked(conn, h)
    dob, last3, letter = _creds(conn, h, victim)
    for i in range(3):
        _, tok = svc.start_call(conn, h, "confirm", NOW + timedelta(minutes=i), pid=victim)
        svc.verify_identity(conn, tok, dob, _wrong(last3), letter, NOW + timedelta(minutes=i))
    _, tok = svc.start_call(conn, h, "confirm", NOW + timedelta(hours=1), pid=victim)
    locked = svc.verify_identity(conn, tok, dob, last3, letter, NOW + timedelta(hours=1))
    return {
        "lockout_after_three_failed_calls": locked["status"] == "locked",
        "ledger_verifies": _ledger_ok(conn, h),
    }


def prompt_injection(conn, h):
    pid = _first_booked(conn, h)
    other = _first_booked(conn, h, "dermatology")
    _, tok = svc.start_call(conn, h, "inbound", NOW)
    body = VerifyIdentity.model_validate(
        {
            **dict(
                zip(("date_of_birth", "id_last3", "id_letter"), _creds(conn, h, pid), strict=True)
            ),
            "pid": other,
        }
    )
    svc.verify_identity(conn, tok, **body.model_dump(), now=NOW)
    appt = svc.get_appointment(conn, tok, NOW)
    return {
        "extra_pid_field_ignored": "pid" not in body.model_dump(),
        "bound_to_verified_patient_only": svc.resolve(conn, tok).pid == pid
        and appt["specialty"] == "cardiology",
    }


def voicemail(conn, h):
    pid = _first_booked(conn, h)
    call_id, tok = svc.start_call(conn, h, "confirm", NOW, pid=pid)
    svc.log_outcome(conn, tok, "voicemail", NOW)
    svc.record_call_outcome(conn, call_id, "voicemail", NOW)
    return {
        "nothing_disclosed": "detail_disclosed" not in _types(conn, h, call_id),
        "outcome_logged": conn.execute(
            "SELECT outcome FROM calls WHERE call_id = %s", (call_id,)
        ).fetchone()[0]
        == "voicemail",
    }


def wrong_number(conn, h):
    pid = _first_booked(conn, h)
    call_id, tok = svc.start_call(conn, h, "confirm", NOW, pid=pid)
    svc.log_outcome(conn, tok, "wrong_number", NOW)
    return {"nothing_disclosed": "detail_disclosed" not in _types(conn, h, call_id)}


def medical_question(conn, h):
    pid = _first_booked(conn, h)
    call_id, tok = _verified_call(conn, h, pid)
    svc.transfer_to_human(conn, tok, "medical question", NOW)
    return {"handed_to_human": "handoff_to_human" in _types(conn, h, call_id)}


def wants_human(conn, h):
    pid = _first_booked(conn, h)
    call_id, tok = svc.start_call(conn, h, "confirm", NOW, pid=pid)
    svc.transfer_to_human(conn, tok, "asked for a person", NOW)
    return {"handed_to_human_even_before_identity": "handoff_to_human" in _types(conn, h, call_id)}


def _freed_slot(conn, h):
    _, tok = _verified_call(conn, h, _first_booked(conn, h))
    svc.cancel_appointment(conn, tok, True, NOW)
    return conn.execute("SELECT slot_id FROM backfills WHERE hospital_id = %s", (h,)).fetchone()[0]


def _waitlist(conn, h):
    return [
        r[0]
        for r in conn.execute(
            "SELECT pid FROM waitlist_entries WHERE hospital_id = %s AND specialty = 'cardiology'"
            " ORDER BY rank",
            (h,),
        )
    ]


def cancel_then_backfill(conn, h):
    slot = _freed_slot(conn, h)
    wl = _waitlist(conn, h)
    first = svc.next_backfill_target(conn, h, slot, NOW)
    c1, _ = svc.start_call(conn, h, "backfill", NOW, pid=wl[0], slot_id=slot)
    svc.record_call_outcome(conn, c1, "no_answer", NOW)
    _, t2 = _verified_call(conn, h, wl[1], "backfill", slot)
    svc.offer_backfill(conn, t2, NOW)
    svc.accept_backfill(conn, t2, NOW + timedelta(minutes=2))
    cid = svc.chain_id(conn, h)
    rep = verify(load_events(conn, cid), load_snapshots(conn, cid))
    return {
        "first_offer_is_rank_1": first["pid"] == wl[0],
        "filled_by_rank_2_after_no_answer": rep.checks["list_order"].status == "pass",
        "ledger_verifies": rep.ok,
    }


def accept_then_late(conn, h):
    slot = _freed_slot(conn, h)
    wl = _waitlist(conn, h)
    _, t1 = _verified_call(conn, h, wl[0], "backfill", slot)
    svc.offer_backfill(conn, t1, NOW)
    svc.sweep(conn, h, NOW + timedelta(minutes=11))
    refused = False
    try:
        svc.accept_backfill(conn, t1, NOW + timedelta(minutes=12))
    except svc.SlotTaken:
        refused = True
    return {
        "late_accept_refused": refused,
        "late_accept_logged": "late_accept_rejected" in _types(conn, h),
        "ledger_verifies": _ledger_ok(conn, h),
    }


def race_two_patients(conn, h):
    slot = _freed_slot(conn, h)
    wl = _waitlist(conn, h)
    jumped = False
    try:
        svc.start_call(conn, h, "backfill", NOW, pid=wl[1], slot_id=slot)
    except svc.NotEligible:
        jumped = True
    _, t1 = _verified_call(conn, h, wl[0], "backfill", slot)
    svc.offer_backfill(conn, t1, NOW)
    svc.accept_backfill(conn, t1, NOW + timedelta(minutes=1))
    filled = conn.execute(
        "SELECT count(*) FROM appointments WHERE hospital_id = %s AND"
        " slot_id = %s AND appointment_id LIKE 'A-BF-%%'",
        (h, slot),
    ).fetchone()[0]
    return {
        "rank_2_cannot_jump_the_queue": jumped,
        "exactly_one_booking": filled == 1,
        "ledger_verifies": _ledger_ok(conn, h),
    }


def opt_out(conn, h):
    pid = _first_booked(conn, h)
    _, tok = _verified_call(conn, h, pid)
    svc.opt_out(conn, tok, NOW)
    blocked = False
    try:
        svc.start_call(conn, h, "confirm", NOW + timedelta(days=1), pid=pid)
    except svc.NotEligible:
        blocked = True
    return {"no_more_automated_calls": blocked}


RUNNERS = {
    "happy-confirm-es": happy_confirm_es,
    "relative-answers": relative_answers,
    "social-engineering": social_engineering,
    "prompt-injection": prompt_injection,
    "voicemail": voicemail,
    "wrong-number": wrong_number,
    "medical-question": medical_question,
    "wants-human": wants_human,
    "cancel-then-backfill": cancel_then_backfill,
    "accept-then-late": accept_then_late,
    "race-two-patients": race_two_patients,
    "opt-out": opt_out,
}


def run(conn, scenario_id: str, run_id: str) -> dict[str, bool]:
    hospital = f"eval-{run_id}-{scenario_id}"
    _setup(conn, hospital)
    return RUNNERS[scenario_id](conn, hospital)
