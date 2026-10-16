"""Generator determinism, calibration and synthetic-only guarantees (eng review 3B)."""

from __future__ import annotations

import re
import statistics

import pytest

from slotback.data import profile as P
from slotback.data.generate import age_on, dataset_hash, generate_day, is_valid_dni

# Pinned on purpose: if the generator's output changes, this fails and the change
# must be deliberate (update the hash and note it in docs/DECISIONS.md).
GOLDEN_HASH = "6ea6f84b7d14f2301c15fcdbfe27b1724a1c4ecdaae641f7f534bb0b962d6f2e"


@pytest.fixture(scope="module")
def day():
    return generate_day()


@pytest.fixture(scope="module")
def many_days():
    return [generate_day(seed=1000 + i) for i in range(50)]


def test_same_seed_same_bytes():
    assert dataset_hash(generate_day(7)) == dataset_hash(generate_day(7))


def test_different_seed_different_data():
    assert dataset_hash(generate_day(7)) != dataset_hash(generate_day(8))


def test_golden_hash_unchanged(day):
    assert dataset_hash(day) == GOLDEN_HASH


def test_shape_of_a_clinic_day(day):
    slots_per_specialty = P.ROOMS_PER_SPECIALTY * (
        (P.DAY_END_MINUTE - P.DAY_START_MINUTE) // P.SLOT_MINUTES
    )
    assert len(day.slots) == len(P.SPECIALTIES) * slots_per_specialty == 400
    assert len(day.appointments) == len(day.slots)
    assert len(day.waitlist) == len(P.SPECIALTIES) * P.WAITLIST_PER_SPECIALTY


def test_mean_propensity_is_calibrated_exactly(day):
    mean = statistics.fmean(a.no_show_propensity for a in day.appointments)
    assert mean == pytest.approx(P.TARGET_NO_SHOW_RATE, abs=1e-4)


def test_realised_no_show_rate_close_to_profile(many_days):
    appts = [a for d in many_days for a in d.appointments]
    rate = sum(a.will_no_show for a in appts) / len(appts)
    assert abs(rate - P.TARGET_NO_SHOW_RATE) <= 0.005


def test_published_associations_hold(many_days):
    """Direction only (see [S2b]): no-shows younger, longer delay, fewer prior visits."""
    shows, no_shows = [], []
    for d in many_days:
        patients = {p.pid: p for p in d.patients}
        for a in d.appointments:
            p = patients[a.pid]
            row = (
                age_on(p.date_of_birth, d.clinic_date),
                a.booking_delay_days,
                p.prior_visits_last_year,
            )
            (no_shows if a.will_no_show else shows).append(row)

    def mean(rows, i):
        return statistics.fmean(r[i] for r in rows)

    assert mean(no_shows, 0) < mean(shows, 0)
    assert mean(no_shows, 1) > mean(shows, 1)
    assert mean(no_shows, 2) < mean(shows, 2)


def test_waitlists_strictly_ranked_without_gaps(day):
    for specialty in P.SPECIALTIES:
        ranks = [w.rank for w in day.waitlist if w.specialty == specialty]
        assert ranks == list(range(1, P.WAITLIST_PER_SPECIALTY + 1))


def test_waitlist_order_is_the_hospitals(day):
    """Preferente before ordinaria, then oldest referral first."""
    for specialty in P.SPECIALTIES:
        entries = sorted(
            (w for w in day.waitlist if w.specialty == specialty), key=lambda w: w.rank
        )
        keys = [(w.priority != "preferente", w.referred_on) for w in entries]
        assert keys == sorted(keys)


def test_booked_and_waiting_patients_are_disjoint(day):
    booked = {a.pid for a in day.appointments}
    waiting = {w.pid for w in day.waitlist}
    assert not booked & waiting
    assert len({p.pid for p in day.patients}) == len(day.patients)


def test_no_generated_id_is_a_valid_dni(many_days):
    assert not any(is_valid_dni(p.id_number) for d in many_days for p in d.patients)


def test_phone_numbers_are_not_dialable(many_days):
    pattern = re.compile(r"^\+34 000 \d{3} \d{3}$")
    assert all(pattern.match(p.phone) for d in many_days for p in d.patients)
