"""Service layer: everything the agent's tools, the dashboard and the webhooks call.

Rules enforced here, not in prompts:
- Tools act only on the patient bound to the call token (D15). Unbound tokens
  (widget, inbound) bind on a successful verify_identity (1C / EOV2).
- Nothing about an appointment is returned before identity is verified, and each
  disclosure is written to the ledger (identity before detail).
- Every state change and its ledger event commit together (record_and_apply, D10).
- Backfill walks the hospital's list in order (domain.backfill); slots are freed
  only by a cancellation or by staff, never by a prediction.
- The showcase hospital is read-only.

All functions take `now` explicitly (fake clock in tests, D22).
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from voiceledger import pg as ledger

from slotback.domain import backfill as bf
from slotback.ledger import EVENT_TYPES


class ServiceError(Exception):
    code = "error"


class Unauthorized(ServiceError):
    code = "unauthorized"


class NotVerified(ServiceError):
    code = "identity_not_verified"


class NotFound(ServiceError):
    code = "not_found"


class ReadOnly(ServiceError):
    code = "read_only"


class CallingPaused(ServiceError):
    code = "calling_paused"


class AlreadyCalled(ServiceError):
    code = "already_called"


class NeedsConfirmation(ServiceError):
    code = "needs_explicit_confirmation"


class SlotTaken(ServiceError):
    code = "slot_taken"


class NotEligible(ServiceError):
    code = "not_eligible"


MAX_FAILURES_PER_CALL = 2
LOCKOUT_FAILED_CALLS = 3
LOCKOUT_WINDOW = timedelta(hours=24)


@dataclass(frozen=True)
class CallCtx:
    call_id: str
    hospital_id: str
    pid: str | None
    purpose: str
    slot_id: str | None
    rank: int | None
    verified: bool
    identity_failures: int


# ── helpers ──────────────────────────────────────────────────────────────────


def chain_id(conn, hospital_id: str) -> str:
    row = conn.execute(
        "SELECT clinic_date FROM hospitals WHERE hospital_id = %s", (hospital_id,)
    ).fetchone()
    if row is None:
        raise NotFound(f"hospital {hospital_id}")
    return f"{hospital_id}:{row[0].isoformat()}"


def _writable(conn, hospital_id: str) -> None:
    row = conn.execute(
        "SELECT read_only FROM hospitals WHERE hospital_id = %s", (hospital_id,)
    ).fetchone()
    if row is None:
        raise NotFound(f"hospital {hospital_id}")
    if row[0]:
        raise ReadOnly(hospital_id)


def _event(conn, hospital_id, now, type, actor="agent", payload=None, slot_id=None, apply=None):
    return ledger.record_and_apply(
        conn,
        chain_id(conn, hospital_id),
        now.isoformat(),
        type,
        actor,
        payload,
        slot_id,
        apply,
        types=EVENT_TYPES,
    )


def resolve(conn, token: str) -> CallCtx:
    row = conn.execute(
        "SELECT call_id, hospital_id, pid, purpose, slot_id, rank, verified, identity_failures"
        " FROM calls WHERE token = %s AND ended_at IS NULL",
        (token,),
    ).fetchone()
    if row is None:
        raise Unauthorized("unknown or finished call")
    return CallCtx(*row)


def _require_verified(ctx: CallCtx) -> None:
    if not ctx.verified or ctx.pid is None:
        raise NotVerified("verify the patient's identity first")


def _is_locked(conn, hospital_id: str, pid: str, now: datetime, exclude_call: str) -> bool:
    n = conn.execute(
        "SELECT count(*) FROM calls WHERE hospital_id = %s AND pid = %s AND call_id <> %s"
        " AND identity_failures > 0 AND NOT verified AND started_at > %s",
        (hospital_id, pid, exclude_call, now - LOCKOUT_WINDOW),
    ).fetchone()[0]
    return n >= LOCKOUT_FAILED_CALLS


# ── calls ────────────────────────────────────────────────────────────────────


def start_call(
    conn,
    hospital_id: str,
    purpose: str,
    now: datetime,
    pid: str | None = None,
    slot_id: str | None = None,
    campaign_key: str | None = None,
    conversation_id: str | None = None,
) -> tuple[str, str]:
    """Create a call and its token. Returns (call_id, token)."""
    _writable(conn, hospital_id)
    paused = conn.execute(
        "SELECT calling_paused FROM settings WHERE hospital_id = %s", (hospital_id,)
    ).fetchone()
    if paused and paused[0] and purpose != "inbound":
        raise CallingPaused("kill switch is on")
    rank = None
    if pid is not None:
        opted = conn.execute(
            "SELECT opted_out FROM patients WHERE hospital_id = %s AND pid = %s",
            (hospital_id, pid),
        ).fetchone()
        if opted is None:
            raise NotFound(pid)
        if opted[0] and purpose != "inbound":
            raise NotEligible("patient opted out of automated calls")
    if purpose == "backfill":
        b = _load_backfill(conn, hospital_id, slot_id)
        if b.current_pid != pid:
            raise NotEligible(f"{pid} is not next on the list for {slot_id}")
        rank = b.rank
    call_id = f"call_{secrets.token_hex(8)}"
    token = secrets.token_urlsafe(24)
    try:
        conn.execute(
            "INSERT INTO calls (call_id, token, hospital_id, pid, purpose, slot_id, rank,"
            " started_at, campaign_key, conversation_id) VALUES"
            " (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                call_id,
                token,
                hospital_id,
                pid,
                purpose,
                slot_id,
                rank,
                now,
                campaign_key,
                conversation_id,
            ),
        )
    except Exception as e:  # unique violation on campaign_key
        if "campaign_key" in str(e):
            raise AlreadyCalled(campaign_key) from e
        raise
    return call_id, token


def record_disclosure(conn, token: str, now: datetime) -> None:
    ctx = resolve(conn, token)
    _event(
        conn,
        ctx.hospital_id,
        now,
        "ai_disclosed",
        payload={"call_id": ctx.call_id},
        slot_id=ctx.slot_id,
    )


# ── identity ─────────────────────────────────────────────────────────────────


def verify_identity(
    conn, token: str, date_of_birth: str, id_last3: str, id_letter: str, now: datetime
) -> dict:
    ctx = resolve(conn, token)
    if ctx.verified:
        return {"status": "verified", "call_purpose": ctx.purpose}
    id_last3, id_letter = id_last3.strip(), id_letter.strip().upper()
    if ctx.pid is not None:
        if _is_locked(conn, ctx.hospital_id, ctx.pid, now, ctx.call_id):
            return _identity_fail(conn, ctx, now, locked=True)
        row = conn.execute(
            "SELECT pid FROM patients WHERE hospital_id = %s AND pid = %s AND date_of_birth = %s"
            " AND substr(id_number, 6, 3) = %s AND right(id_number, 1) = %s",
            (ctx.hospital_id, ctx.pid, date_of_birth, id_last3, id_letter),
        ).fetchone()
        match = row[0] if row else None
    else:
        rows = conn.execute(
            "SELECT pid FROM patients WHERE hospital_id = %s AND date_of_birth = %s"
            " AND substr(id_number, 6, 3) = %s AND right(id_number, 1) = %s",
            (ctx.hospital_id, date_of_birth, id_last3, id_letter),
        ).fetchall()
        match = rows[0][0] if len(rows) == 1 else None
        if match and _is_locked(conn, ctx.hospital_id, match, now, ctx.call_id):
            return _identity_fail(conn, ctx, now, locked=True)
    if match is None:
        return _identity_fail(conn, ctx, now)

    def bind(c):
        c.execute(
            "UPDATE calls SET verified = true, pid = %s WHERE call_id = %s", (match, ctx.call_id)
        )

    payload = {"call_id": ctx.call_id, "pid": match}
    if ctx.rank is not None:
        payload["rank"] = ctx.rank
    _event(
        conn,
        ctx.hospital_id,
        now,
        "identity_verified",
        payload=payload,
        slot_id=ctx.slot_id,
        apply=bind,
    )
    # The agent learns why it is calling only after identity: a confirm call must never
    # be treated as a backfill offer (found on the first real phone call, 2026-10-16).
    return {"status": "verified", "call_purpose": ctx.purpose}


def _identity_fail(conn, ctx: CallCtx, now: datetime, locked: bool = False) -> dict:
    failures = ctx.identity_failures + 1
    end = locked or failures >= MAX_FAILURES_PER_CALL

    def bump(c):
        c.execute(
            "UPDATE calls SET identity_failures = %s WHERE call_id = %s", (failures, ctx.call_id)
        )

    payload = {"call_id": ctx.call_id, "pid": ctx.pid, "locked": locked, "failures": failures}
    if ctx.rank is not None and end:
        payload["rank"] = ctx.rank  # closes this rank for the backfill (logged reason)
    _event(
        conn,
        ctx.hospital_id,
        now,
        "identity_failed",
        payload=payload,
        slot_id=ctx.slot_id if end else None,
        apply=bump,
    )
    if end and ctx.purpose == "backfill":
        _close_rank(conn, ctx.hospital_id, ctx.slot_id, ctx.pid, "identity_failed", now, log=False)
    if locked:
        return {"status": "locked", "say": "callback_number_only"}
    return {
        "status": "end_call" if end else "failed",
        "attempts_left": max(0, MAX_FAILURES_PER_CALL - failures),
    }


# ── appointments ─────────────────────────────────────────────────────────────


def _upcoming(conn, ctx: CallCtx):
    row = conn.execute(
        "SELECT a.appointment_id, a.slot_id, a.specialty, s.starts_at, a.status"
        " FROM appointments a JOIN slots s USING (hospital_id, slot_id)"
        " WHERE a.hospital_id = %s AND a.pid = %s AND a.status IN ('scheduled', 'confirmed')"
        " ORDER BY s.starts_at LIMIT 1",
        (ctx.hospital_id, ctx.pid),
    ).fetchone()
    if row is None:
        raise NotFound("no upcoming appointment")
    return row


def get_appointment(conn, token: str, now: datetime) -> dict:
    ctx = resolve(conn, token)
    _require_verified(ctx)
    appointment_id, slot_id, specialty, starts_at, status = _upcoming(conn, ctx)
    _event(
        conn,
        ctx.hospital_id,
        now,
        "detail_disclosed",
        payload={"call_id": ctx.call_id, "pid": ctx.pid, "fields": ["specialty", "starts_at"]},
    )
    return {
        "appointment_id": appointment_id,
        "specialty": specialty,
        "starts_at": starts_at.isoformat(timespec="minutes"),
        "status": status,
    }


def confirm_appointment(conn, token: str, now: datetime) -> dict:
    ctx = resolve(conn, token)
    _require_verified(ctx)
    _writable(conn, ctx.hospital_id)
    appointment_id, slot_id, *_ = _upcoming(conn, ctx)
    _event(
        conn, ctx.hospital_id, now, "read_back", payload={"call_id": ctx.call_id, "pid": ctx.pid}
    )

    def apply(c):
        c.execute(
            "UPDATE appointments SET status = 'confirmed' WHERE hospital_id = %s"
            " AND appointment_id = %s",
            (ctx.hospital_id, appointment_id),
        )

    _event(
        conn,
        ctx.hospital_id,
        now,
        "appointment_confirmed",
        payload={"call_id": ctx.call_id, "pid": ctx.pid, "appointment_id": appointment_id},
        slot_id=slot_id,
        apply=apply,
    )
    return {"status": "confirmed"}


def cancel_appointment(conn, token: str, patient_confirmed: bool, now: datetime) -> dict:
    """Only after the agent read the appointment back and heard an explicit yes (D19)."""
    ctx = resolve(conn, token)
    _require_verified(ctx)
    _writable(conn, ctx.hospital_id)
    if not patient_confirmed:
        raise NeedsConfirmation("read the appointment back and get an explicit yes")
    appointment_id, slot_id, *_ = _upcoming(conn, ctx)

    def apply(c):
        c.execute(
            "UPDATE appointments SET status = 'cancelled' WHERE hospital_id = %s"
            " AND appointment_id = %s",
            (ctx.hospital_id, appointment_id),
        )

    _event(
        conn,
        ctx.hospital_id,
        now,
        "appointment_cancelled",
        payload={"call_id": ctx.call_id, "pid": ctx.pid, "appointment_id": appointment_id},
        slot_id=slot_id,
        apply=apply,
    )
    free_slot(conn, ctx.hospital_id, slot_id, "cancellation", "agent", now)
    return {"status": "cancelled", "slot_released": True}


def _open_slots(conn, hospital_id: str, specialty: str, now: datetime) -> list:
    return conn.execute(
        "SELECT s.slot_id, s.starts_at FROM slots s"
        " LEFT JOIN backfills b USING (hospital_id, slot_id)"
        " WHERE s.hospital_id = %s AND s.specialty = %s AND s.status = 'unfilled'"
        " AND s.starts_at > %s AND (b.status IS NULL OR b.status = 'unfilled')"
        " ORDER BY s.starts_at LIMIT 5",
        (hospital_id, specialty, now),
    ).fetchall()


def list_alternative_slots(conn, token: str, now: datetime) -> dict:
    ctx = resolve(conn, token)
    _require_verified(ctx)
    _, _, specialty, _, _ = _upcoming(conn, ctx)
    slots = _open_slots(conn, ctx.hospital_id, specialty, now)
    return {
        "slots": [{"slot_id": s, "starts_at": t.isoformat(timespec="minutes")} for s, t in slots]
    }


def reschedule(conn, token: str, new_slot_id: str, now: datetime) -> dict:
    """Atomic swap: book the new slot and release the old one in one transaction."""
    ctx = resolve(conn, token)
    _require_verified(ctx)
    _writable(conn, ctx.hospital_id)
    appointment_id, old_slot, specialty, _, _ = _upcoming(conn, ctx)
    open_ids = {s for s, _ in _open_slots(conn, ctx.hospital_id, specialty, now)}
    if new_slot_id not in open_ids:
        raise SlotTaken(new_slot_id)

    def swap(c):
        n = c.execute(
            "UPDATE slots SET status = 'filled', version = version + 1"
            " WHERE hospital_id = %s AND slot_id = %s AND status = 'unfilled'",
            (ctx.hospital_id, new_slot_id),
        ).rowcount
        if n != 1:
            raise SlotTaken(new_slot_id)
        c.execute(
            "UPDATE appointments SET slot_id = %s, status = 'scheduled'"
            " WHERE hospital_id = %s AND appointment_id = %s",
            (new_slot_id, ctx.hospital_id, appointment_id),
        )
        c.execute(
            "UPDATE slots SET status = 'freed', version = version + 1"
            " WHERE hospital_id = %s AND slot_id = %s",
            (ctx.hospital_id, old_slot),
        )

    _event(
        conn,
        ctx.hospital_id,
        now,
        "appointment_rescheduled",
        payload={
            "call_id": ctx.call_id,
            "pid": ctx.pid,
            "appointment_id": appointment_id,
            "from": old_slot,
            "to": new_slot_id,
        },
        slot_id=old_slot,
        apply=swap,
    )
    free_slot(conn, ctx.hospital_id, old_slot, "reschedule", "agent", now, already_freed=True)
    return {"status": "rescheduled", "slot_id": new_slot_id}


# ── backfill ─────────────────────────────────────────────────────────────────


def _load_backfill(conn, hospital_id: str, slot_id: str | None, lock: bool = False) -> bf.Backfill:
    row = conn.execute(
        "SELECT b.status, b.ranked_pids, b.rank, b.hold_until, b.filled_by, s.starts_at"
        " FROM backfills b JOIN slots s USING (hospital_id, slot_id)"
        " WHERE b.hospital_id = %s AND b.slot_id = %s" + (" FOR UPDATE OF b" if lock else ""),
        (hospital_id, slot_id),
    ).fetchone()
    if row is None:
        raise NotFound(f"no backfill for {slot_id}")
    status, pids, rank, hold_until, filled_by, starts_at = row
    return bf.Backfill(
        slot_id, starts_at, tuple(pids), bf.Status(status), rank, hold_until, filled_by
    )


def _save_backfill(conn, hospital_id: str, b: bf.Backfill) -> None:
    conn.execute(
        "UPDATE backfills SET status = %s, rank = %s, hold_until = %s, filled_by = %s"
        " WHERE hospital_id = %s AND slot_id = %s",
        (b.status.value, b.rank, b.hold_until, b.filled_by, hospital_id, b.slot_id),
    )
    if b.status in (bf.Status.FILLED, bf.Status.UNFILLED):
        conn.execute(
            "UPDATE slots SET status = %s, version = version + 1"
            " WHERE hospital_id = %s AND slot_id = %s",
            (b.status.value, hospital_id, b.slot_id),
        )


def free_slot(
    conn,
    hospital_id: str,
    slot_id: str,
    reason: str,
    actor: str,
    now: datetime,
    already_freed: bool = False,
) -> dict:
    """Free a slot and snapshot the hospital's list. Reason: cancellation | staff | reschedule."""
    if reason not in ("cancellation", "staff", "reschedule"):
        raise ValueError("slots are freed only by a cancellation, a reschedule or staff")
    _writable(conn, hospital_id)
    specialty, starts_at = conn.execute(
        "SELECT specialty, starts_at FROM slots WHERE hospital_id = %s AND slot_id = %s",
        (hospital_id, slot_id),
    ).fetchone()
    pids = [
        r[0]
        for r in conn.execute(
            "SELECT pid FROM waitlist_entries WHERE hospital_id = %s AND specialty = %s"
            " ORDER BY rank",
            (hospital_id, specialty),
        )
    ]
    cid = chain_id(conn, hospital_id)
    snapshot_id = f"snap-{slot_id}-{now:%H%M%S}"

    def mark(c):
        if not already_freed:
            c.execute(
                "UPDATE slots SET status = 'freed', version = version + 1"
                " WHERE hospital_id = %s AND slot_id = %s",
                (hospital_id, slot_id),
            )

    _event(conn, hospital_id, now, "slot_freed", actor, {"reason": reason}, slot_id, mark)
    domain = bf.take_snapshot(bf.Backfill(slot_id, starts_at, tuple(pids)), now)

    def store(c):
        h = ledger.save_snapshot(c, cid, snapshot_id, pids)
        store.hash = h
        c.execute(
            "INSERT INTO backfills (hospital_id, slot_id, status, snapshot_id, ranked_pids, rank)"
            " VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (hospital_id, slot_id) DO UPDATE SET"
            " status = EXCLUDED.status, snapshot_id = EXCLUDED.snapshot_id,"
            " ranked_pids = EXCLUDED.ranked_pids, rank = EXCLUDED.rank, hold_until = NULL,"
            " filled_by = NULL",
            (hospital_id, slot_id, "offering", snapshot_id, json.dumps(pids), 1),
        )

    from voiceledger.chain import snapshot_hash

    _event(
        conn,
        hospital_id,
        now,
        "list_snapshot",
        "system",
        {"snapshot_id": snapshot_id, "snapshot_hash": snapshot_hash(pids), "specialty": specialty},
        slot_id,
        store,
    )
    if domain.status is bf.Status.UNFILLED:
        _finish_unfilled(conn, hospital_id, domain, "cut-off reached", now)
    return {"slot_id": slot_id, "status": domain.status.value, "candidates": len(pids)}


def _finish_unfilled(conn, hospital_id, b: bf.Backfill, reason: str, now: datetime) -> None:
    def apply(c):
        _save_backfill(c, hospital_id, b)

    _event(conn, hospital_id, now, "slot_unfilled", "system", {"reason": reason}, b.slot_id, apply)


def next_backfill_target(conn, hospital_id: str, slot_id: str, now: datetime) -> dict | None:
    """Who to call next, skipping (and logging) patients who opted out."""
    while True:
        b = _load_backfill(conn, hospital_id, slot_id)
        b, _ = bf.sweep(b, now)
        if b.status is not bf.Status.OFFERING:
            return None
        pid = b.current_pid
        opted = conn.execute(
            "SELECT opted_out FROM patients WHERE hospital_id = %s AND pid = %s",
            (hospital_id, pid),
        ).fetchone()[0]
        if not opted:
            return {"pid": pid, "rank": b.rank}
        _event(
            conn,
            hospital_id,
            now,
            "rank_skipped",
            "system",
            {"pid": pid, "rank": b.rank, "reason": "opted_out"},
            slot_id,
            lambda c, b=b, pid=pid: _save_backfill(
                c, hospital_id, bf.close_rank(b, pid, "ineligible", now)
            ),
        )


class _AlreadyMovedOn(Exception):
    """Aborts the transaction (and its ledger event) when the rank is already closed."""


def _close_rank(
    conn, hospital_id, slot_id, pid, reason, now, log=True, event_type=None, payload=None
):
    def apply(c):
        b = _load_backfill(c, hospital_id, slot_id, lock=True)
        if b.status is not bf.Status.OFFERING or b.current_pid != pid:
            raise _AlreadyMovedOn  # idempotent webhook / sweep got there first
        nb = bf.close_rank(b, pid, reason, now)
        _save_backfill(c, hospital_id, nb)
        apply.after = nb

    apply.after = None
    try:
        if log:
            _event(conn, hospital_id, now, event_type, "agent", payload, slot_id, apply)
        else:
            with conn.transaction():
                apply(conn)
    except _AlreadyMovedOn:
        return
    nb = apply.after
    if nb is not None and nb.status is bf.Status.UNFILLED:
        _event(
            conn,
            hospital_id,
            now,
            "slot_unfilled",
            "system",
            {"reason": "list exhausted" if nb.rank > len(nb.ranked_pids) else "cut-off reached"},
            slot_id,
        )


def offer_backfill(conn, token: str, now: datetime) -> dict:
    ctx = resolve(conn, token)
    _require_verified(ctx)
    if ctx.purpose != "backfill":
        raise NotEligible("not a backfill call")
    b = _load_backfill(conn, ctx.hospital_id, ctx.slot_id)
    nb = bf.start_offer(b, ctx.pid, now)
    specialty, starts_at = conn.execute(
        "SELECT specialty, starts_at FROM slots WHERE hospital_id = %s AND slot_id = %s",
        (ctx.hospital_id, ctx.slot_id),
    ).fetchone()
    base = {"call_id": ctx.call_id, "pid": ctx.pid, "rank": b.rank}
    _event(
        conn,
        ctx.hospital_id,
        now,
        "detail_disclosed",
        payload={**base, "fields": ["specialty", "slot_time"]},
        slot_id=ctx.slot_id,
    )
    _event(
        conn,
        ctx.hospital_id,
        now,
        "offer_started",
        payload={**base, "hold_until": nb.hold_until.isoformat()},
        slot_id=ctx.slot_id,
        apply=lambda c: _save_backfill(c, ctx.hospital_id, nb),
    )
    return {
        "specialty": specialty,
        "starts_at": starts_at.isoformat(timespec="minutes"),
        "hold_minutes": int(bf.HOLD.total_seconds() // 60),
    }


def accept_backfill(conn, token: str, now: datetime) -> dict:
    ctx = resolve(conn, token)
    _require_verified(ctx)
    base = {"call_id": ctx.call_id, "pid": ctx.pid, "rank": ctx.rank}
    try:

        def claim(c):
            b = _load_backfill(c, ctx.hospital_id, ctx.slot_id, lock=True)
            claim.after = bf.accept(b, ctx.pid, now)  # raises LateAccept
            _save_backfill(c, ctx.hospital_id, claim.after)
            appt = f"A-BF-{ctx.slot_id}"
            c.execute(
                "INSERT INTO appointments (hospital_id, appointment_id, slot_id, pid, specialty,"
                " booked_on, booking_delay_days, no_show_propensity, will_no_show, status)"
                " SELECT %s, %s, %s, %s, specialty, %s, 0, 0, false, 'confirmed' FROM slots"
                " WHERE hospital_id = %s AND slot_id = %s",
                (
                    ctx.hospital_id,
                    appt,
                    ctx.slot_id,
                    ctx.pid,
                    now.date(),
                    ctx.hospital_id,
                    ctx.slot_id,
                ),
            )

        _event(
            conn,
            ctx.hospital_id,
            now,
            "offer_accepted",
            payload=base,
            slot_id=ctx.slot_id,
            apply=claim,
        )
    except bf.LateAccept:
        _event(
            conn, ctx.hospital_id, now, "late_accept_rejected", payload=base, slot_id=ctx.slot_id
        )
        raise SlotTaken("this slot is no longer available") from None
    _event(conn, ctx.hospital_id, now, "read_back", payload=base, slot_id=ctx.slot_id)
    _event(conn, ctx.hospital_id, now, "slot_filled", "system", base, ctx.slot_id)
    return {"status": "booked"}


def decline_backfill(conn, token: str, now: datetime) -> dict:
    ctx = resolve(conn, token)
    _require_verified(ctx)
    _close_rank(
        conn,
        ctx.hospital_id,
        ctx.slot_id,
        ctx.pid,
        "declined",
        now,
        event_type="offer_declined",
        payload={"call_id": ctx.call_id, "pid": ctx.pid, "rank": ctx.rank},
    )
    return {"status": "declined"}


CALL_OUTCOMES = {"no_answer", "voicemail", "busy", "wrong_number", "completed", "failed"}


def record_call_outcome(
    conn, call_id: str, outcome: str, now: datetime, conversation_id: str | None = None
) -> dict:
    """From the signed post-call webhook (EOV1). Idempotent."""
    if outcome not in CALL_OUTCOMES:
        raise ValueError(outcome)
    row = conn.execute(
        "SELECT hospital_id, pid, purpose, slot_id, rank, ended_at FROM calls WHERE call_id = %s",
        (call_id,),
    ).fetchone()
    if row is None:
        raise NotFound(call_id)
    hospital_id, pid, purpose, slot_id, rank, ended_at = row
    if ended_at is not None:
        return {"status": "already_recorded"}
    conn.execute(
        "UPDATE calls SET ended_at = %s, outcome = COALESCE(outcome, %s),"
        " conversation_id = COALESCE(conversation_id, %s) WHERE call_id = %s",
        (now, outcome, conversation_id, call_id),
    )
    if purpose == "backfill" and outcome in bf.CLOSING_REASONS:
        _close_rank(
            conn,
            hospital_id,
            slot_id,
            pid,
            outcome,
            now,
            event_type="call_attempt",
            payload={"call_id": call_id, "pid": pid, "rank": rank, "outcome": outcome},
        )
    elif outcome in ("no_answer", "voicemail", "busy", "wrong_number"):
        _event(
            conn,
            hospital_id,
            now,
            "call_attempt",
            payload={"call_id": call_id, "pid": pid, "outcome": outcome},
        )
    return {"status": "recorded"}


def sweep(conn, hospital_id: str, now: datetime) -> dict:
    """Timer (EOV1): expire lapsed holds and apply cut-offs. Safe to run any time."""
    expired, unfilled = 0, 0
    slot_ids = [
        r[0]
        for r in conn.execute(
            "SELECT slot_id FROM backfills WHERE hospital_id = %s AND status = 'offering'",
            (hospital_id,),
        )
    ]
    for slot_id in slot_ids:
        b = _load_backfill(conn, hospital_id, slot_id)
        nb, gone = bf.sweep(b, now)
        if gone:
            expired += 1
            _event(
                conn,
                hospital_id,
                now,
                "offer_expired",
                "system",
                {"pid": gone, "rank": b.rank},
                slot_id,
                lambda c, nb=nb: _save_backfill(c, hospital_id, nb),
            )
            # The call may still be live: mark the outcome but keep the token usable so a
            # late "yes" is refused *and* logged (late_accept_rejected), not silently dropped.
            conn.execute(
                "UPDATE calls SET outcome = COALESCE(outcome, 'hold_expired')"
                " WHERE hospital_id = %s AND slot_id = %s AND pid = %s",
                (hospital_id, slot_id, gone),
            )
        if nb.status is bf.Status.UNFILLED:
            unfilled += 1
            _finish_unfilled(
                conn,
                hospital_id,
                nb,
                "list exhausted" if nb.rank > len(nb.ranked_pids) else "cut-off reached",
                now,
            )
    return {"expired": expired, "unfilled": unfilled}


# ── handoff, opt-out, outcomes ───────────────────────────────────────────────


def transfer_to_human(conn, token: str, reason: str, now: datetime) -> dict:
    ctx = resolve(conn, token)
    _event(
        conn,
        ctx.hospital_id,
        now,
        "handoff_to_human",
        payload={"call_id": ctx.call_id, "pid": ctx.pid, "reason": reason[:200]},
        slot_id=ctx.slot_id,
    )
    # No live transfer in the demo: the request is logged and admissions calls back.
    # Production would use a SIP transfer to the admissions queue (docs/05).
    return {"status": "callback_requested"}


def opt_out(conn, token: str, now: datetime) -> dict:
    ctx = resolve(conn, token)
    _require_verified(ctx)

    def apply(c):
        c.execute(
            "UPDATE patients SET opted_out = true WHERE hospital_id = %s AND pid = %s",
            (ctx.hospital_id, ctx.pid),
        )

    _event(
        conn,
        ctx.hospital_id,
        now,
        "opted_out",
        payload={"call_id": ctx.call_id, "pid": ctx.pid},
        apply=apply,
    )
    return {"status": "opted_out"}


def log_outcome(conn, token: str, outcome: str, now: datetime) -> dict:
    ctx = resolve(conn, token)
    conn.execute("UPDATE calls SET outcome = %s WHERE call_id = %s", (outcome[:60], ctx.call_id))
    return {"status": "logged"}


def mark_attendance(
    conn, hospital_id: str, appointment_id: str, attended: bool, now: datetime
) -> None:
    """Staff/system records attendance, needed for billing (OV3)."""
    pid, slot_id = conn.execute(
        "SELECT pid, slot_id FROM appointments WHERE hospital_id = %s AND appointment_id = %s",
        (hospital_id, appointment_id),
    ).fetchone()
    status = "attended" if attended else "no_show"

    def apply(c):
        c.execute(
            "UPDATE appointments SET status = %s WHERE hospital_id = %s AND appointment_id = %s",
            (status, hospital_id, appointment_id),
        )

    _event(
        conn,
        hospital_id,
        now,
        status,
        "staff",
        {"pid": pid, "appointment_id": appointment_id},
        slot_id,
        apply,
    )
