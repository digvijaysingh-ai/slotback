"""Property tests for the pure backfill state machine (fast, no DB; eng EOV6)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from slotback.domain.backfill import (
    HOLD,
    TRANSITIONS,
    Backfill,
    Ev,
    IllegalTransition,
    LateAccept,
    Status,
    accept,
    close_rank,
    staff_booked,
    start_offer,
    sweep,
    take_snapshot,
    transition,
)

NOW = datetime(2026, 10, 14, 10, 0)
START = datetime(2026, 10, 16, 11, 40)  # 2 days ahead: before the cut-off


def fresh(n=5, start=START):
    return Backfill("S-1", start, tuple(f"P-{i}" for i in range(1, n + 1)))


def test_every_unlisted_transition_is_illegal():
    for status in Status:
        for ev in Ev:
            if (status, ev) not in TRANSITIONS:
                with pytest.raises(IllegalTransition):
                    transition(status, ev)


def test_terminal_states_accept_nothing():
    for status in (Status.FILLED, Status.UNFILLED):
        assert not [k for k in TRANSITIONS if k[0] is status]


actions = st.lists(
    st.tuples(
        st.sampled_from(["offer", "close", "accept_now", "accept_late", "sweep", "intruder"]),
        st.integers(min_value=0, max_value=30),  # minutes passing
    ),
    max_size=40,
)


@settings(max_examples=300)
@given(st.integers(min_value=1, max_value=8), actions)
def test_offers_follow_list_order_and_fill_at_most_once(n, steps):
    b = take_snapshot(fresh(n), NOW)
    now = NOW
    offered: list[int] = []
    for action, minutes in steps:
        now += timedelta(minutes=minutes)
        pid = b.current_pid
        try:
            if action == "offer" and pid:
                b = start_offer(b, pid, now)
                offered.append(b.rank)
            elif action == "close" and pid:
                b = close_rank(b, pid, "no_answer", now)
            elif action == "accept_now" and pid and b.hold_until:
                b = accept(b, pid, min(now, b.hold_until))
            elif action == "accept_late" and pid and b.hold_until:
                b = accept(b, pid, b.hold_until + timedelta(seconds=1))
            elif action == "intruder":
                b = accept(b, "P-intruder", now)
            elif action == "sweep":
                b, _ = sweep(b, now)
        except LateAccept:
            pass
        except IllegalTransition:
            assert b.status in (Status.FILLED, Status.UNFILLED)
    # Ranks were offered in non-decreasing order: never back to an earlier patient.
    assert offered == sorted(offered)
    # A fill is always the patient at the current rank, never an intruder.
    if b.status is Status.FILLED:
        assert b.filled_by == b.ranked_pids[b.rank - 1]
    assert b.rank <= n + 1


def test_hold_expires_and_moves_to_next_rank():
    b = start_offer(take_snapshot(fresh(), NOW), "P-1", NOW)
    b, expired = sweep(b, NOW + HOLD + timedelta(seconds=1))
    assert expired == "P-1" and b.current_pid == "P-2"


def test_late_accept_after_expiry_is_rejected():
    b = start_offer(take_snapshot(fresh(), NOW), "P-1", NOW)
    with pytest.raises(LateAccept):
        accept(b, "P-1", NOW + HOLD + timedelta(seconds=1))


def test_cannot_offer_out_of_order():
    b = take_snapshot(fresh(), NOW)
    with pytest.raises(IllegalTransition):
        start_offer(b, "P-2", NOW)


def test_exhausted_list_is_unfilled():
    b = take_snapshot(fresh(2), NOW)
    b = close_rank(b, "P-1", "voicemail", NOW)
    b = close_rank(b, "P-2", "declined", NOW)
    assert b.status is Status.UNFILLED


def test_cutoff_stops_offering():
    b = take_snapshot(fresh(start=NOW + timedelta(hours=25)), NOW)
    b, _ = sweep(b, NOW + timedelta(hours=2))
    assert b.status is Status.UNFILLED


def test_snapshot_inside_cutoff_never_offers():
    b = take_snapshot(fresh(start=NOW + timedelta(hours=3)), NOW)
    assert b.status is Status.UNFILLED and b.current_pid is None


def test_staff_can_book_while_offering():
    b = staff_booked(take_snapshot(fresh(), NOW))
    assert b.status is Status.FILLED and b.filled_by == "staff"
    with pytest.raises(LateAccept):
        accept(b, "P-1", NOW)


def test_unknown_closing_reason_rejected():
    b = take_snapshot(fresh(), NOW)
    with pytest.raises(ValueError):
        close_rank(b, "P-1", "predicted_no_show", NOW)
