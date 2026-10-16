"""Backfill state machine for one freed slot. Pure: no I/O, the clock is passed in.

The agent never decides priority: it walks the hospital's ranked list one patient
at a time and only moves on after a logged closing reason.

    FREED ──snapshot──▶ OFFERING(rank k) ──accept within hold──▶ FILLED
                          │  ▲
                          │  └── close(k): no_answer | voicemail | busy | wrong_number |
                          │                identity_failed | declined | hold_expired |
                          │                ineligible            → rank k+1
                          ├── list exhausted ───────────────▶ UNFILLED
                          ├── cut-off reached (start - 24h) ─▶ UNFILLED
                          └── staff booked it ──────────────▶ FILLED (by staff)

Any (state, event) pair not in TRANSITIONS raises IllegalTransition.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

HOLD = timedelta(minutes=10)
CUTOFF_BEFORE_START = timedelta(hours=24)


class Status(StrEnum):
    FREED = "freed"
    OFFERING = "offering"
    FILLED = "filled"
    UNFILLED = "unfilled"


class Ev(StrEnum):
    SNAPSHOT = "snapshot"
    OFFER = "offer"  # identity verified, offer read out, hold starts
    CLOSE = "close"  # rank k closed with a logged reason
    ACCEPT = "accept"
    EXHAUSTED = "exhausted"
    CUTOFF = "cutoff"
    STAFF_BOOKED = "staff_booked"


TRANSITIONS: dict[tuple[Status, Ev], Status] = {
    (Status.FREED, Ev.SNAPSHOT): Status.OFFERING,
    (Status.FREED, Ev.STAFF_BOOKED): Status.FILLED,
    (Status.OFFERING, Ev.OFFER): Status.OFFERING,
    (Status.OFFERING, Ev.CLOSE): Status.OFFERING,
    (Status.OFFERING, Ev.ACCEPT): Status.FILLED,
    (Status.OFFERING, Ev.EXHAUSTED): Status.UNFILLED,
    (Status.OFFERING, Ev.CUTOFF): Status.UNFILLED,
    (Status.OFFERING, Ev.STAFF_BOOKED): Status.FILLED,
}

CLOSING_REASONS = frozenset(
    {
        "no_answer",
        "voicemail",
        "busy",
        "wrong_number",
        "identity_failed",
        "declined",
        "hold_expired",
        "ineligible",
    }
)


class IllegalTransition(Exception):
    pass


class LateAccept(Exception):
    """Accept arrived for a patient who no longer holds the offer. Logged, never honoured."""


def transition(status: Status, event: Ev) -> Status:
    try:
        return TRANSITIONS[(status, event)]
    except KeyError:
        raise IllegalTransition(f"{event} not allowed from {status}") from None


@dataclass(frozen=True)
class Backfill:
    slot_id: str
    slot_start: datetime
    ranked_pids: tuple[str, ...]  # the hospital's order at snapshot time
    status: Status = Status.FREED
    rank: int = 0  # 0 until the snapshot is taken
    hold_until: datetime | None = None
    filled_by: str | None = None  # pid, or "staff"

    @property
    def current_pid(self) -> str | None:
        if self.status is Status.OFFERING and 1 <= self.rank <= len(self.ranked_pids):
            return self.ranked_pids[self.rank - 1]
        return None

    @property
    def cutoff(self) -> datetime:
        return self.slot_start - CUTOFF_BEFORE_START


def take_snapshot(b: Backfill, now: datetime) -> Backfill:
    b = replace(b, status=transition(b.status, Ev.SNAPSHOT), rank=1)
    return _settle(b, now)


def start_offer(b: Backfill, pid: str, now: datetime) -> Backfill:
    if pid != b.current_pid:
        raise IllegalTransition(f"offer to {pid} but rank {b.rank} is {b.current_pid}")
    transition(b.status, Ev.OFFER)
    return replace(b, hold_until=now + HOLD)


def close_rank(b: Backfill, pid: str, reason: str, now: datetime) -> Backfill:
    if reason not in CLOSING_REASONS:
        raise ValueError(f"not a closing reason: {reason}")
    if pid != b.current_pid:
        raise IllegalTransition(f"closing {pid} but rank {b.rank} is {b.current_pid}")
    transition(b.status, Ev.CLOSE)
    return _settle(replace(b, rank=b.rank + 1, hold_until=None), now)


def accept(b: Backfill, pid: str, now: datetime) -> Backfill:
    """Raises LateAccept for anyone but the current holder within the hold window."""
    if b.status is not Status.OFFERING or pid != b.current_pid:
        raise LateAccept(f"{pid} does not hold the offer for {b.slot_id}")
    if b.hold_until is None or now > b.hold_until:
        raise LateAccept(f"hold for {pid} expired")
    return replace(b, status=transition(b.status, Ev.ACCEPT), filled_by=pid, hold_until=None)


def staff_booked(b: Backfill) -> Backfill:
    return replace(b, status=transition(b.status, Ev.STAFF_BOOKED), filled_by="staff")


def sweep(b: Backfill, now: datetime) -> tuple[Backfill, str | None]:
    """Timer: expire a lapsed hold (returns the expired pid) and apply the cut-off."""
    expired = None
    if b.status is Status.OFFERING and b.hold_until is not None and now > b.hold_until:
        expired = b.current_pid
        b = replace(b, rank=b.rank + 1, hold_until=None)
    return _settle(b, now), expired


def _settle(b: Backfill, now: datetime) -> Backfill:
    if b.status is not Status.OFFERING:
        return b
    if now >= b.cutoff:
        return replace(b, status=transition(b.status, Ev.CUTOFF), hold_until=None)
    if b.rank > len(b.ranked_pids):
        return replace(b, status=transition(b.status, Ev.EXHAUSTED), hold_until=None)
    return b
