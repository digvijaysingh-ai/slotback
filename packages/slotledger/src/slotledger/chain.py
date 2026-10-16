"""Hash chain primitives. Pure functions, no storage.

Each event is hashed over its canonical JSON plus the previous event's hash:

    hash_n = sha256( prev_hash_n || canonical_json(event_n without "hash") )

so changing, inserting, deleting or reordering any event breaks every later link.
One chain per hospital per day (chain_id = "<hospital_id>:<YYYY-MM-DD>").
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

GENESIS = "0" * 64

# Care events (identity, disclosure, read-back, handoff) are first-class so the
# verifier can prove "identity before detail".
EVENT_TYPES = frozenset(
    {
        "slot_freed",
        "list_snapshot",
        "call_attempt",
        "identity_verified",
        "identity_failed",
        "ai_disclosed",
        "detail_disclosed",
        "read_back",
        "offer_started",
        "offer_accepted",
        "offer_declined",
        "offer_expired",
        "late_accept_rejected",
        "rank_skipped",
        "handoff_to_human",
        "opted_out",
        "slot_filled",
        "slot_unfilled",
        "appointment_confirmed",
        "appointment_cancelled",
        "appointment_rescheduled",
        "attended",
        "no_show",
    }
)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class Event:
    chain_id: str
    seq: int
    ts: str
    type: str
    actor: str  # "agent" | "system" | "staff"
    payload: dict = field(default_factory=dict)
    slot_id: str | None = None
    prev_hash: str = GENESIS
    hash: str = ""

    def body(self) -> dict:
        d = asdict(self)
        d.pop("hash")
        return d

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def from_dict(cls, d: dict) -> Event:
        return cls(**d)


def event_hash(body: dict) -> str:
    return hashlib.sha256((body["prev_hash"] + canonical_json(body)).encode("utf-8")).hexdigest()


def seal(
    chain_id: str,
    seq: int,
    ts: str,
    type: str,
    actor: str,
    payload: dict | None = None,
    slot_id: str | None = None,
    prev_hash: str = GENESIS,
) -> Event:
    if type not in EVENT_TYPES:
        raise ValueError(f"unknown event type: {type}")
    unsealed = Event(chain_id, seq, ts, type, actor, payload or {}, slot_id, prev_hash)
    return Event(**{**asdict(unsealed), "hash": event_hash(unsealed.body())})


def append(events: list[Event], ts: str, type: str, actor: str, **kw) -> Event:
    """In-memory append, used by tests and the replay. Storage uses record_and_apply."""
    chain_id = kw.pop("chain_id", events[0].chain_id if events else "demo:1970-01-01")
    prev = events[-1] if events else None
    ev = seal(
        chain_id,
        (prev.seq + 1) if prev else 1,
        ts,
        type,
        actor,
        prev_hash=prev.hash if prev else GENESIS,
        **kw,
    )
    events.append(ev)
    return ev


def snapshot_hash(ordered_pids: list[str]) -> str:
    return hashlib.sha256(canonical_json(ordered_pids).encode("utf-8")).hexdigest()
