"""Slotback's ledger: voiceledger with Slotback's event types and its two rules.

The rules (identity before detail, list order) are declared in voiceops.toml [ledger], so
the API, the dashboard, the evals and an auditor's `voiceledger verify --rules
voiceops.toml` all check the same things.
"""

from __future__ import annotations

from pathlib import Path

import voiceledger
from voiceledger import Report, SignedHead, load_rules_file
from voiceledger.chain import Event

ROOT = Path(__file__).resolve().parents[1]
RULES = load_rules_file(ROOT / "voiceops.toml")

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


def verify(
    events: list[Event],
    snapshots: dict[str, list[str]] | None = None,
    head: SignedHead | None = None,
    trusted_public_key: str | None = None,
) -> Report:
    return voiceledger.verify(events, snapshots, head, trusted_public_key, rules=RULES)
