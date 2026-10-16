"""Replay a ledger and prove its invariants.

Checks (each reports pass | fail | not_checked, plus the first failing seq):

  chain                  seq contiguous from 1, one chain_id, every prev_hash links,
                         every hash recomputes.
  identity_before_detail every detail_disclosed(call_id, pid) comes after an
                         identity_verified for the same call and patient.
  list_order             (needs snapshots) per freed slot, offers follow the hospital's
                         snapshot: rank 1, 2, 3... with the right patient at each rank,
                         and a rank is only left after a logged closing reason.
  head                   (needs a signed head) Ed25519 signature valid, head matches the
                         last event; key matches the trusted key if one is given.

Rank lifecycle per slot (anything else fails list_order):

  cur=1 ─▶ event for rank cur ──closing event──▶ cur+1
                │                                  closing = call_attempt{no_answer,
                ├─ offer_accepted ─▶ slot_filled          voicemail, busy, wrong_number}
                └─ late_accept_rejected (any rank, ignored) | identity_failed | offer_declined
                                                            | offer_expired | rank_skipped
"""

from __future__ import annotations

from dataclasses import dataclass, field

from slotledger.chain import GENESIS, Event, event_hash, snapshot_hash
from slotledger.sign import SignedHead, verify_head

CLOSING_OUTCOMES = frozenset({"no_answer", "voicemail", "busy", "wrong_number"})
CLOSING_TYPES = frozenset({"identity_failed", "offer_declined", "offer_expired", "rank_skipped"})
RANKED_TYPES = frozenset(
    {
        "call_attempt",
        "identity_verified",
        "identity_failed",
        "offer_started",
        "offer_accepted",
        "offer_declined",
        "offer_expired",
        "rank_skipped",
        "slot_filled",
    }
)


@dataclass
class Check:
    status: str = "pass"  # pass | fail | not_checked
    detail: str = ""
    seq: int | None = None

    def fail(self, seq: int | None, detail: str) -> None:
        if self.status != "fail":  # keep the first failure
            self.status, self.seq, self.detail = "fail", seq, detail


@dataclass
class Report:
    events: int
    checks: dict[str, Check] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(c.status != "fail" for c in self.checks.values())

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "events": self.events,
            "checks": {k: vars(v) for k, v in self.checks.items()},
        }


def check_chain(events: list[Event]) -> Check:
    c = Check()
    if not events:
        c.status, c.detail = "not_checked", "empty ledger"
        return c
    chain_id = events[0].chain_id
    prev = GENESIS
    for i, ev in enumerate(events, start=1):
        if ev.chain_id != chain_id:
            c.fail(ev.seq, f"chain_id changed to {ev.chain_id}")
        elif ev.seq != i:
            c.fail(ev.seq, f"expected seq {i}")
        elif ev.prev_hash != prev:
            c.fail(ev.seq, "prev_hash does not link to the previous event")
        elif event_hash(ev.body()) != ev.hash:
            c.fail(ev.seq, "event was changed after it was recorded")
        prev = ev.hash
    if c.status == "pass":
        c.detail = f"{len(events)} events linked"
    return c


def check_identity_before_detail(events: list[Event]) -> Check:
    c = Check()
    verified: set[tuple[str, str]] = set()
    disclosures = 0
    for ev in events:
        key = (ev.payload.get("call_id", ""), ev.payload.get("pid", ""))
        if ev.type == "identity_verified":
            verified.add(key)
        elif ev.type == "detail_disclosed":
            disclosures += 1
            if key not in verified:
                c.fail(ev.seq, f"detail disclosed before identity verified (call {key[0]})")
    if c.status == "pass":
        c.detail = f"{disclosures} disclosures, all after verification"
    return c


def check_list_order(events: list[Event], snapshots: dict[str, list[str]] | None) -> Check:
    c = Check()
    if snapshots is None:
        c.status, c.detail = "not_checked", "no snapshots supplied (ledger-only upload)"
        return c
    state: dict[str, dict] = {}  # slot_id -> {"pids": [...], "cur": int, "accepted": pid}
    slots_checked = 0
    for ev in events:
        if ev.slot_id is None:
            continue
        if ev.type == "list_snapshot":
            sid = ev.payload.get("snapshot_id")
            pids = snapshots.get(sid)
            if pids is None:
                c.fail(ev.seq, f"snapshot {sid} missing from bundle")
                continue
            if snapshot_hash(pids) != ev.payload.get("snapshot_hash"):
                c.fail(ev.seq, f"snapshot {sid} does not match its recorded hash")
                continue
            state[ev.slot_id] = {"pids": pids, "cur": 1, "accepted": None}
            slots_checked += 1
            continue
        st = state.get(ev.slot_id)
        if st is None or ev.type not in RANKED_TYPES or "rank" not in ev.payload:
            continue
        rank, pid = ev.payload["rank"], ev.payload.get("pid")
        if rank != st["cur"]:
            c.fail(ev.seq, f"rank {rank} acted on while rank {st['cur']} was still open")
            continue
        if rank > len(st["pids"]) or st["pids"][rank - 1] != pid:
            c.fail(ev.seq, f"patient at rank {rank} does not match the hospital's list")
            continue
        if ev.type == "offer_accepted":
            st["accepted"] = pid
        elif ev.type == "slot_filled" and st["accepted"] != pid:
            c.fail(ev.seq, "slot filled without an accepted offer from this patient")
        elif ev.type in CLOSING_TYPES or (
            ev.type == "call_attempt" and ev.payload.get("outcome") in CLOSING_OUTCOMES
        ):
            st["cur"] += 1
    if c.status == "pass":
        c.detail = f"{slots_checked} freed slots offered in list order"
    return c


def verify(
    events: list[Event],
    snapshots: dict[str, list[str]] | None = None,
    head: SignedHead | None = None,
    trusted_public_key: str | None = None,
) -> Report:
    report = Report(events=len(events))
    report.checks["chain"] = check_chain(events)
    report.checks["identity_before_detail"] = check_identity_before_detail(events)
    report.checks["list_order"] = check_list_order(events, snapshots)
    report.checks["head"] = verify_head(head, events[-1] if events else None, trusted_public_key)
    return report
