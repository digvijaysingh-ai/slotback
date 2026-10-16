"""The simulated day runs through the real services and leaves a verifiable ledger."""

from __future__ import annotations

import json
from pathlib import Path

from slotback.sim.day import simulate_day

ROOT = Path(__file__).resolve().parents[1]


def test_simulated_day_is_consistent_and_verifiable(pg):
    r = simulate_day(pg, "sim", seed=7)
    assert r.ledger_ok and r.privacy_leaks == 0
    assert r.confirm_calls == 400
    assert r.filled + r.unfilled == r.freed
    assert r.confirmed + r.freed <= r.contacted <= r.confirm_calls
    assert 0 <= r.billable_recovered <= r.attended_backfilled <= r.filled


def test_simulation_is_reproducible(pg):
    a = simulate_day(pg, "sim-a", seed=11)
    b = simulate_day(pg, "sim-b", seed=11)
    assert (a.freed, a.filled, a.backfill_calls) == (b.freed, b.filled, b.backfill_calls)


def test_every_registry_number_has_a_provenance_tag():
    reg = json.loads((ROOT / "metrics" / "registry.json").read_text())
    for key, entry in reg.items():
        if key.startswith("_"):
            continue
        assert entry["provenance"] in {
            "SIMULATED",
            "BENCHMARK",
            "SYNTHETIC",
            "MEASURED",
            "ASSUMPTION",
        }, key
        if entry["provenance"] == "BENCHMARK":
            assert entry["source"] and entry["year"], key
