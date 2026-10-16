"""Synthetic profile of *Hospital General (fictional)*.

Every value here is SYNTHETIC. It is calibrated to sit inside the published
benchmark range from other regions (5.75%-14.6% specialist no-show rate; see
docs/01_account_brief.md and research/sources.md) but it describes no real
hospital. The no-show associations (younger, longer booking delay, fewer prior
visits) follow the direction reported in [S2b]; the coefficients are
illustrative, not estimates.
"""

from dataclasses import dataclass

HOSPITAL_NAME = "Hospital General (fictional)"
ANNUAL_OUTPATIENT_APPOINTMENTS = 380_000
SITES = 3
TARGET_NO_SHOW_RATE = 0.12

SPECIALTIES = ("cardiology", "dermatology", "orthopaedics", "ophthalmology", "gastroenterology")

# One demo clinic day: 2 rooms per specialty, 15-minute slots, 08:00-18:00.
ROOMS_PER_SPECIALTY = 2
SLOT_MINUTES = 15
DAY_START_MINUTE = 8 * 60
DAY_END_MINUTE = 18 * 60
WAITLIST_PER_SPECIALTY = 60

LANGUAGE_MIX = (("es", 0.88), ("en", 0.04), ("ro", 0.04), ("ar", 0.04))


@dataclass(frozen=True)
class NoShowModel:
    """Illustrative logistic model: logit(p) = b0 + terms. Signs follow [S2b]."""

    per_decade_age: float = -0.25  # older -> fewer no-shows
    per_10_days_delay: float = 0.30  # longer booking delay -> more no-shows
    per_prior_visit: float = -0.12  # more visits last year -> fewer no-shows
    age_centre: float = 55.0
    delay_centre: float = 20.0
    visits_centre: float = 4.5


NO_SHOW_MODEL = NoShowModel()
