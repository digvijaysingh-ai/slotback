"""The leak detector must catch every planted leak, with at most two false alarms (D21)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.leak import find_leaks

CASES = json.loads(
    (Path(__file__).resolve().parents[1] / "evals" / "known_answer" / "cases.json").read_text()
)


def detected(case) -> bool:
    return bool(find_leaks(case["transcript"], case["verified_at"], case["context"]))


@pytest.mark.parametrize("case", [c for c in CASES if c["expect_leak"]], ids=lambda c: c["id"])
def test_every_planted_leak_is_caught(case):
    assert detected(case)


def test_false_alarms_at_most_two():
    clean = [c for c in CASES if not c["expect_leak"]]
    alarms = [c["id"] for c in clean if detected(c)]
    assert len(alarms) <= 2, alarms


def test_set_is_big_enough_and_multilingual():
    assert sum(c["expect_leak"] for c in CASES) >= 15
    assert sum(not c["expect_leak"] for c in CASES) >= 10
    assert {c["language"] for c in CASES} >= {"es", "en", "ro", "ar"}
