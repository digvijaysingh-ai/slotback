"""Simulate one confirmation campaign + backfill day through the REAL service layer.

Everything this produces is SIMULATED. Patient behaviour comes from the ASSUMPTIONS
below (seeded, so the run is reproducible); none of it is a measured result.

    campaign day (09:00-20:00, three days before the clinic day)
      for each appointment: confirm call ─▶ answered / voicemail / no answer
          answered + would-no-show ─▶ maybe cancels ─▶ slot freed ─▶ backfill
      backfill: walk the hospital's list: no answer / voicemail / decline / accept
    clinic day: attendance recorded for backfilled patients (billing needs it)
"""

from __future__ import annotations

import random
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from voiceledger.pg import load_events, load_snapshots

from slotback.data.generate import generate_day
from slotback.data.seed import load_dataset
from slotback.ledger import verify
from slotback.services import scheduling as svc


@dataclass(frozen=True)
class Assumptions:
    """Behaviour parameters: ILLUSTRATIVE, not estimates. Each is shown on the dashboard."""

    p_answer: float = 0.65  # confirmation call answered
    p_voicemail: float = 0.20  # else voicemail; remainder no answer
    p_cancel_if_would_miss: float = 0.45  # a would-be no-show cancels when reached
    p_backfill_answer: float = 0.60
    p_backfill_voicemail: float = 0.25
    p_backfill_accept: float = 0.55  # verified patient accepts the offered slot
    p_attend_backfilled: float = 0.90
    # SMS-only counterfactual (no calls): share of would-be no-shows who cancel by SMS,
    # and share of those freed slots staff manage to refill by hand.
    sms_cancel_share: float = 0.25
    staff_refill_rate: float = 0.35


DEFAULT_ASSUMPTIONS = Assumptions()


@dataclass
class DayResult:
    hospital_id: str
    appointments: int
    confirm_calls: int
    contacted: int
    confirmed: int
    freed: int
    backfill_calls: int
    filled: int
    unfilled: int
    attended_backfilled: int
    median_minutes_to_fill: float | None
    sms_only_recovered: float
    billable_recovered: int
    privacy_leaks: int
    ledger_ok: bool
    events: int


def _creds(conn, hospital_id, pid):
    dob, idn = conn.execute(
        "SELECT date_of_birth, id_number FROM patients WHERE hospital_id = %s AND pid = %s",
        (hospital_id, pid),
    ).fetchone()
    return dob.isoformat(), idn[5:8], idn[-1]


def _answered_confirm(conn, rng, a, hospital_id, token, appt_pid, will_miss, t):
    svc.record_disclosure(conn, token, t)
    dob, last3, letter = _creds(conn, hospital_id, appt_pid)
    if rng.random() < 0.03:  # occasional mis-heard digits, then corrected
        svc.verify_identity(conn, token, dob, "999" if last3 != "999" else "998", letter, t)
    svc.verify_identity(conn, token, dob, last3, letter, t)
    svc.get_appointment(conn, token, t)
    if will_miss and rng.random() < a.p_cancel_if_would_miss:
        svc.cancel_appointment(conn, token, True, t)
        svc.log_outcome(conn, token, "cancelled", t)
        return "cancelled"
    svc.confirm_appointment(conn, token, t)
    svc.log_outcome(conn, token, "confirmed", t)
    return "confirmed"


def _backfill(conn, rng, a, hospital_id, slot_id, t):
    calls, filled_at = 0, None
    while True:
        target = svc.next_backfill_target(conn, hospital_id, slot_id, t)
        if target is None:
            break
        t += timedelta(minutes=3)
        call_id, token = svc.start_call(
            conn, hospital_id, "backfill", t, pid=target["pid"], slot_id=slot_id
        )
        calls += 1
        r = rng.random()
        if r < a.p_backfill_answer:
            svc.record_disclosure(conn, token, t)
            svc.verify_identity(conn, token, *_creds(conn, hospital_id, target["pid"]), now=t)
            svc.offer_backfill(conn, token, t)
            t += timedelta(minutes=1)
            if rng.random() < a.p_backfill_accept:
                svc.accept_backfill(conn, token, t)
                svc.log_outcome(conn, token, "backfill_booked", t)
                svc.record_call_outcome(conn, call_id, "completed", t)
                filled_at = t
                break
            svc.decline_backfill(conn, token, t)
            svc.log_outcome(conn, token, "backfill_declined", t)
            svc.record_call_outcome(conn, call_id, "completed", t)
        elif r < a.p_backfill_answer + a.p_backfill_voicemail:
            svc.record_call_outcome(conn, call_id, "voicemail", t)
        else:
            svc.record_call_outcome(conn, call_id, "no_answer", t)
    return calls, filled_at, t


def simulate_day(
    conn,
    hospital_id: str,
    seed: int = 20261016,
    clinic_date: str = "2026-10-16",
    assumptions: Assumptions | None = None,
) -> DayResult:
    a = assumptions or DEFAULT_ASSUMPTIONS
    rng = random.Random(seed * 7 + 1)
    ds = generate_day(seed, clinic_date)
    load_dataset(conn, ds, hospital_id)
    campaign = datetime.fromisoformat(clinic_date) - timedelta(days=3)
    t = campaign.replace(hour=9)
    starts = {sl.slot_id: sl.start for sl in ds.slots}
    appts = sorted(ds.appointments, key=lambda x: (starts[x.slot_id], x.slot_id))
    step = timedelta(minutes=(11 * 60) / len(appts))  # spread across 09:00-20:00
    contacted = confirmed = freed = backfill_calls = filled = 0
    fill_minutes: list[float] = []
    for i, ap in enumerate(appts):
        t = campaign.replace(hour=9) + step * i
        call_id, token = svc.start_call(
            conn,
            hospital_id,
            "confirm",
            t,
            pid=ap.pid,
            campaign_key=f"{ap.appointment_id}:{campaign.date()}",
        )
        r = rng.random()
        if r < a.p_answer:
            contacted += 1
            outcome = _answered_confirm(
                conn, rng, a, hospital_id, token, ap.pid, ap.will_no_show, t
            )
            svc.record_call_outcome(conn, call_id, "completed", t)
            if outcome == "confirmed":
                confirmed += 1
            else:
                freed += 1
                n, filled_at, _ = _backfill(conn, rng, a, hospital_id, ap.slot_id, t)
                backfill_calls += n
                if filled_at is not None:
                    filled += 1
                    fill_minutes.append((filled_at - t).total_seconds() / 60)
        elif r < a.p_answer + a.p_voicemail:
            svc.record_call_outcome(conn, call_id, "voicemail", t)
        else:
            svc.record_call_outcome(conn, call_id, "no_answer", t)

    # Clinic day: attendance for backfilled patients (needed for billing, OV3).
    clinic_t = datetime.fromisoformat(clinic_date).replace(hour=20)
    attended = 0
    for (appointment_id,) in conn.execute(
        "SELECT appointment_id FROM appointments WHERE hospital_id = %s"
        " AND appointment_id LIKE 'A-BF-%%' ORDER BY appointment_id",
        (hospital_id,),
    ).fetchall():
        came = rng.random() < a.p_attend_backfilled
        attended += came
        svc.mark_attendance(conn, hospital_id, appointment_id, came, clinic_t)

    would_miss = sum(ap.will_no_show for ap in ds.appointments)
    sms_freed = would_miss * a.sms_cancel_share
    sms_only = sms_freed * a.staff_refill_rate
    baseline = freed * a.staff_refill_rate  # slots staff would have refilled anyway
    cid = svc.chain_id(conn, hospital_id)
    events = load_events(conn, cid)
    report = verify(events, load_snapshots(conn, cid))
    return DayResult(
        hospital_id=hospital_id,
        appointments=len(appts),
        confirm_calls=len(appts),
        contacted=contacted,
        confirmed=confirmed,
        freed=freed,
        backfill_calls=backfill_calls,
        filled=filled,
        unfilled=freed - filled,
        attended_backfilled=attended,
        median_minutes_to_fill=round(statistics.median(fill_minutes), 1) if fill_minutes else None,
        sms_only_recovered=round(sms_only, 1),
        billable_recovered=max(0, attended - round(baseline)),
        privacy_leaks=0 if report.checks["identity_before_detail"].status == "pass" else 1,
        ledger_ok=report.ok,
        events=len(events),
    )


def result_dict(r: DayResult, a: Assumptions | None = None) -> dict:
    a = a or DEFAULT_ASSUMPTIONS
    return {"result": asdict(r), "assumptions": asdict(a)}
