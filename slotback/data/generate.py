"""Deterministic synthetic data for one clinic day.

Pure functions only: same seed -> byte-identical output (see dataset_hash).
Nothing here can identify a real person:

- names are random combinations of common Spanish given names and surnames;
- phone numbers use the "+34 000" prefix, which is not a valid Spanish number,
  so they cannot be dialled (the only dialable number is the allow-listed demo
  phone from the environment, never stored here);
- ID numbers are 8 random digits whose check letter is deliberately shifted, so
  no generated ID passes the official DNI checksum.

    generate_day(seed)
      ├─ patients   (booked + waiting list, disjoint)
      ├─ slots      (rooms x 15-min, 08:00-18:00, per specialty)
      ├─ appointments (one per slot, with illustrative no-show propensity)
      └─ waitlist   (per specialty, ranked 1..n by the *hospital's* order)
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

from slotback.data import profile as P

GIVEN_NAMES = (
    "María",
    "Carmen",
    "Josefa",
    "Isabel",
    "Ana",
    "Lucía",
    "Laura",
    "Marta",
    "Elena",
    "Pilar",
    "Rosa",
    "Cristina",
    "Antonio",
    "José",
    "Manuel",
    "Francisco",
    "David",
    "Juan",
    "Javier",
    "Daniel",
    "Carlos",
    "Miguel",
    "Pedro",
    "Alejandro",
    "Pablo",
    "Sergio",
    "Andrea",
    "Sofía",
    "Ioana",
    "Andrei",
    "Fatima",
    "Youssef",
    "James",
    "Emma",
)
SURNAMES = (
    "García",
    "Rodríguez",
    "González",
    "Fernández",
    "López",
    "Martínez",
    "Sánchez",
    "Pérez",
    "Gómez",
    "Martín",
    "Jiménez",
    "Ruiz",
    "Hernández",
    "Díaz",
    "Moreno",
    "Muñoz",
    "Álvarez",
    "Romero",
    "Alonso",
    "Gutiérrez",
    "Navarro",
    "Torres",
    "Domínguez",
    "Vázquez",
    "Ramos",
    "Gil",
    "Ramírez",
    "Serrano",
    "Blanco",
    "Molina",
    "Popescu",
    "Ionescu",
    "El Amrani",
    "Smith",
)
DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


@dataclass(frozen=True)
class Patient:
    pid: str  # pseudonymous id, the only identifier used outside the DB
    given_name: str
    surname: str
    date_of_birth: str
    id_number: str  # synthetic, fails the official checksum by construction
    phone: str  # "+34 000 ..." non-dialable
    language: str
    hearing_difficulty: bool
    prior_visits_last_year: int


@dataclass(frozen=True)
class Slot:
    slot_id: str
    specialty: str
    room: int
    start: str  # ISO datetime, local Europe/Madrid
    minutes: int


@dataclass(frozen=True)
class Appointment:
    appointment_id: str
    slot_id: str
    pid: str
    specialty: str
    booked_on: str
    booking_delay_days: int
    no_show_propensity: float  # ILLUSTRATIVE, never used to free a slot
    will_no_show: bool  # drawn from the propensity, for simulation only


@dataclass(frozen=True)
class WaitlistEntry:
    specialty: str
    rank: int  # 1 = next to be offered; order set by the hospital
    pid: str
    priority: str  # "preferente" | "ordinaria" (hospital-assigned)
    referred_on: str


@dataclass
class Dataset:
    seed: int
    clinic_date: str
    hospital: str = P.HOSPITAL_NAME
    patients: list[Patient] = field(default_factory=list)
    slots: list[Slot] = field(default_factory=list)
    appointments: list[Appointment] = field(default_factory=list)
    waitlist: list[WaitlistEntry] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def dataset_hash(ds: Dataset) -> str:
    return hashlib.sha256(ds.to_json().encode("utf-8")).hexdigest()


def synthetic_id_number(rng: random.Random) -> str:
    """8 digits + a check letter shifted by one, so it is never a valid DNI."""
    digits = rng.randrange(10_000_000, 100_000_000)
    valid = DNI_LETTERS[digits % 23]
    shifted = DNI_LETTERS[(DNI_LETTERS.index(valid) + 1) % 23]
    return f"{digits}{shifted}"


def is_valid_dni(id_number: str) -> bool:
    return id_number[-1] == DNI_LETTERS[int(id_number[:-1]) % 23]


def _pick_language(rng: random.Random) -> str:
    r = rng.random()
    acc = 0.0
    for lang, share in P.LANGUAGE_MIX:
        acc += share
        if r < acc:
            return lang
    return P.LANGUAGE_MIX[0][0]


def _make_patient(rng: random.Random, n: int, clinic_day: date) -> Patient:
    age = min(95, max(18, round(rng.gauss(55, 17))))
    dob = clinic_day - timedelta(days=age * 365 + rng.randrange(0, 365))
    return Patient(
        pid=f"P-{n:05d}",
        given_name=rng.choice(GIVEN_NAMES),
        surname=f"{rng.choice(SURNAMES)} {rng.choice(SURNAMES)}",
        date_of_birth=dob.isoformat(),
        id_number=synthetic_id_number(rng),
        phone=f"+34 000 {rng.randrange(0, 1000):03d} {rng.randrange(0, 1000):03d}",
        language=_pick_language(rng),
        hearing_difficulty=rng.random() < (0.04 + max(0, age - 65) * 0.012),
        prior_visits_last_year=min(20, _poisson(rng, 4.5)),
    )


def _poisson(rng: random.Random, lam: float) -> int:
    # Knuth; fine for small lambda and keeps us on stdlib random (deterministic).
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def age_on(dob: str, on: str) -> int:
    b, d = date.fromisoformat(dob), date.fromisoformat(on)
    return d.year - b.year - ((d.month, d.day) < (b.month, b.day))


def _logit_terms(age: int, delay: int, visits: int) -> float:
    m = P.NO_SHOW_MODEL
    return (
        m.per_decade_age * (age - m.age_centre) / 10
        + m.per_10_days_delay * (delay - m.delay_centre) / 10
        + m.per_prior_visit * (visits - m.visits_centre)
    )


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def calibrate_intercept(terms: list[float], target: float) -> float:
    """Bisection on b0 so the mean propensity equals `target` exactly (to 1e-9)."""
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        mean = sum(_sigmoid(mid + t) for t in terms) / len(terms)
        lo, hi = (mid, hi) if mean < target else (lo, mid)
    return (lo + hi) / 2


def generate_day(seed: int = 20261016, clinic_date: str = "2026-10-16") -> Dataset:
    rng = random.Random(seed)
    day = date.fromisoformat(clinic_date)
    ds = Dataset(seed=seed, clinic_date=clinic_date)
    n = 0

    # Slots and the patients booked into them.
    booked: list[tuple[Slot, Patient, int]] = []
    for specialty in P.SPECIALTIES:
        for room in range(1, P.ROOMS_PER_SPECIALTY + 1):
            for minute in range(P.DAY_START_MINUTE, P.DAY_END_MINUTE, P.SLOT_MINUTES):
                start = f"{clinic_date}T{minute // 60:02d}:{minute % 60:02d}:00"
                slot = Slot(
                    f"S-{specialty[:3].upper()}-{room}-{minute:04d}",
                    specialty,
                    room,
                    start,
                    P.SLOT_MINUTES,
                )
                n += 1
                patient = _make_patient(rng, n, day)
                delay = max(1, round(rng.gammavariate(2.0, 10.0)))  # mean ~20 days
                ds.slots.append(slot)
                ds.patients.append(patient)
                booked.append((slot, patient, delay))

    terms = [
        _logit_terms(age_on(p.date_of_birth, clinic_date), delay, p.prior_visits_last_year)
        for _, p, delay in booked
    ]
    b0 = calibrate_intercept(terms, P.TARGET_NO_SHOW_RATE)
    for (slot, patient, delay), t in zip(booked, terms, strict=True):
        propensity = _sigmoid(b0 + t)
        ds.appointments.append(
            Appointment(
                appointment_id=f"A-{slot.slot_id[2:]}",
                slot_id=slot.slot_id,
                pid=patient.pid,
                specialty=slot.specialty,
                booked_on=(day - timedelta(days=delay)).isoformat(),
                booking_delay_days=delay,
                no_show_propensity=round(propensity, 6),
                will_no_show=rng.random() < propensity,
            )
        )

    # Waiting lists: the *hospital* orders them (priority, then referral date).
    for specialty in P.SPECIALTIES:
        entries = []
        for _ in range(P.WAITLIST_PER_SPECIALTY):
            n += 1
            patient = _make_patient(rng, n, day)
            ds.patients.append(patient)
            priority = "preferente" if rng.random() < 0.2 else "ordinaria"
            referred = day - timedelta(days=rng.randrange(10, 240))
            entries.append((priority != "preferente", referred, patient.pid, priority))
        entries.sort()
        for rank, (_, referred, pid, priority) in enumerate(entries, start=1):
            ds.waitlist.append(WaitlistEntry(specialty, rank, pid, priority, referred.isoformat()))

    return ds
