"""Build the read-only showcase day, its signed evidence bundle and the metrics registry.

    uv run python -m slotback.sim.showcase            # writes evidence/ and metrics/

- Runs simulate_day() on hospital "showcase" (clinic day 2026-10-16), then marks it
  read-only so nothing (evals included) can change it.
- Signs the day's head with LEDGER_SIGNING_KEY; the matching public key is written
  to evidence/trusted_key.txt (the key the "hospital" would hold).
- Writes metrics/registry.json: every number with its provenance tag (D28 / eng 2C).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from voiceledger import sign_head, write_bundle
from voiceledger.pg import load_events, load_snapshots
from voiceledger.sign import public_key_hex

from slotback.db import apply_schema
from slotback.localdb import database_url
from slotback.services.scheduling import chain_id
from slotback.sim.day import Assumptions, simulate_day

ROOT = Path(__file__).resolve().parents[2]
HOSPITAL, CLINIC_DATE, SEED = "showcase", "2026-10-16", 20261016

BENCHMARKS = {
    "benchmark_cost_per_missed_eur": {
        "value": 61.3,
        "provenance": "BENCHMARK",
        "source": "S2",
        "year": "2013-14",
        "note": "€3,386,919 ÷ 55,249 missed appointments, our calculation",
    },
    "benchmark_no_show_rate_reference": {
        "value": 0.138,
        "provenance": "BENCHMARK",
        "source": "S2",
        "year": "2013-14",
        "note": "Reference health area, 400,761 appointments",
    },
    "benchmark_forgot_or_communication_share": {
        "value": 0.46,
        "provenance": "BENCHMARK",
        "source": "S2",
        "year": "2013-14",
        "note": "Forgot 29.6% + communication failure 16.0% (Table 26)",
    },
}


def build_registry(r, a: Assumptions, cost_per_slot_eur: float | None) -> dict:
    sim = lambda v, note: {"value": v, "provenance": "SIMULATED", "note": note}  # noqa: E731
    syn = lambda v, note: {"value": v, "provenance": "SYNTHETIC", "note": note}  # noqa: E731
    reg = {
        "_about": "Every number shown on the dashboard, docs and readout comes from here. "
        "SIMULATED = output of slotback.sim on synthetic data with the assumptions listed; "
        "BENCHMARK = published figure from another region with source and year; "
        "SYNTHETIC = property of the generated data. Nothing here is a measured result.",
        "appointments": syn(r.appointments, "Synthetic clinic day, 5 specialties"),
        "hospital_no_show_rate": syn(0.12, "Synthetic profile of Hospital General (fictional)"),
        "confirm_calls": sim(r.confirm_calls, "Confirmation calls placed"),
        "contact_rate": sim(round(r.contacted / r.confirm_calls, 3), "Share of calls answered"),
        "confirmed": sim(r.confirmed, "Appointments confirmed"),
        "freed_slots": sim(r.freed, "Slots freed by a cancellation during the call"),
        "backfill_calls": sim(r.backfill_calls, "Calls to the waiting list"),
        "recovered_slots": sim(r.filled, "Freed slots refilled by the agent, in list order"),
        "unfilled_slots": sim(r.unfilled, "Freed slots not refilled"),
        "fill_rate": sim(round(r.filled / r.freed, 3) if r.freed else None, "Refilled ÷ freed"),
        "median_time_to_fill_min": sim(r.median_minutes_to_fill, "From release to booking"),
        "attended_backfilled": sim(r.attended_backfilled, "Backfilled patients who attended"),
        "billable_recovered_slots": sim(
            r.billable_recovered,
            "Attended backfills minus the slots staff would have refilled anyway "
            f"(staff_refill_rate = {a.staff_refill_rate})",
        ),
        "sms_only_recovered_slots": sim(
            r.sms_only_recovered,
            f"Counterfactual: would-be no-shows × sms_cancel_share ({a.sms_cancel_share}) × "
            f"staff_refill_rate ({a.staff_refill_rate})",
        ),
        "privacy_leaks": sim(r.privacy_leaks, "Ledger verifier: identity before detail"),
        "ledger_events": sim(r.events, "Events in the signed showcase ledger"),
        "cost_per_recovered_slot_eur": sim(
            cost_per_slot_eur, "Estimated platform cost ÷ recovered slots (see assumptions)"
        ),
        "assumptions": {"provenance": "ASSUMPTION", "value": a.__dict__},
        **BENCHMARKS,
    }
    return reg


def estimate_cost_per_slot(r, minutes_per_call: float = 1.5, eur_per_min: float = 0.075):
    """ASSUMPTION: ~1.5 billed minutes per call at ~$0.08/min (pricing page 2026-10-16)."""
    if not r.filled:
        return None
    calls = r.confirm_calls + r.backfill_calls
    return round(calls * minutes_per_call * eur_per_min / r.filled, 2)


def main() -> None:
    load_dotenv()
    key = os.environ.get("LEDGER_SIGNING_KEY")
    url = database_url(str(ROOT / ".data" / "pg-showcase"))
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS showcase_build CASCADE")
        conn.execute("CREATE SCHEMA showcase_build")
        conn.execute("SET search_path TO showcase_build")
        apply_schema(conn)
        a = Assumptions()
        r = simulate_day(conn, HOSPITAL, SEED, CLINIC_DATE, a)
        conn.execute("UPDATE hospitals SET read_only = true WHERE hospital_id = %s", (HOSPITAL,))
        cid = chain_id(conn, HOSPITAL)
        events, snaps = load_events(conn, cid), load_snapshots(conn, cid)
    head = None
    if key:
        head = sign_head(key, cid, events[-1].seq, events[-1].hash, f"{CLINIC_DATE}T21:00:00")
        (ROOT / "evidence" / "trusted_key.txt").write_text(public_key_hex(key) + "\n")
    else:
        print("LEDGER_SIGNING_KEY not set: bundle is UNSIGNED")
    out = ROOT / "evidence" / f"showcase-{CLINIC_DATE}.zip"
    out.write_bytes(write_bundle(events, snaps, head))
    registry = build_registry(r, a, estimate_cost_per_slot(r))
    (ROOT / "metrics" / "registry.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps({k: v for k, v in r.__dict__.items()}, indent=2))
    print(f"wrote {out.relative_to(ROOT)} ({len(events)} events, signed={head is not None})")


if __name__ == "__main__":
    main()
