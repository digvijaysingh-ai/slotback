"""Load a generated Dataset into Postgres under one hospital_id.

Usage:  uv run python -m slotback.data.seed --hospital showcase --read-only
"""

from __future__ import annotations

import argparse

import psycopg
from dotenv import load_dotenv

from slotback.data.generate import Dataset, generate_day
from slotback.db import apply_schema, database_url


class HospitalExists(Exception):
    pass


def load_dataset(
    conn: psycopg.Connection, ds: Dataset, hospital_id: str, read_only: bool = False
) -> None:
    """Insert everything in one transaction. Refuses to overwrite an existing hospital."""
    with conn.transaction():
        exists = conn.execute(
            "SELECT 1 FROM hospitals WHERE hospital_id = %s", (hospital_id,)
        ).fetchone()
        if exists:
            raise HospitalExists(hospital_id)
        conn.execute(
            "INSERT INTO hospitals (hospital_id, name, clinic_date, seed, read_only)"
            " VALUES (%s, %s, %s, %s, %s)",
            (hospital_id, ds.hospital, ds.clinic_date, ds.seed, read_only),
        )
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO patients (hospital_id, pid, given_name, surname, date_of_birth,"
                " id_number, phone, language, hearing_difficulty, prior_visits_last_year)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        hospital_id,
                        p.pid,
                        p.given_name,
                        p.surname,
                        p.date_of_birth,
                        p.id_number,
                        p.phone,
                        p.language,
                        p.hearing_difficulty,
                        p.prior_visits_last_year,
                    )
                    for p in ds.patients
                ],
            )
            cur.executemany(
                "INSERT INTO slots (hospital_id, slot_id, specialty, room, starts_at, minutes)"
                " VALUES (%s, %s, %s, %s, %s, %s)",
                [
                    (hospital_id, s.slot_id, s.specialty, s.room, s.start, s.minutes)
                    for s in ds.slots
                ],
            )
            cur.executemany(
                "INSERT INTO appointments (hospital_id, appointment_id, slot_id, pid, specialty,"
                " booked_on, booking_delay_days, no_show_propensity, will_no_show)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        hospital_id,
                        a.appointment_id,
                        a.slot_id,
                        a.pid,
                        a.specialty,
                        a.booked_on,
                        a.booking_delay_days,
                        a.no_show_propensity,
                        a.will_no_show,
                    )
                    for a in ds.appointments
                ],
            )
            cur.executemany(
                "INSERT INTO waitlist_entries (hospital_id, specialty, rank, pid, priority,"
                " referred_on) VALUES (%s, %s, %s, %s, %s, %s)",
                [
                    (hospital_id, w.specialty, w.rank, w.pid, w.priority, w.referred_on)
                    for w in ds.waitlist
                ],
            )


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hospital", required=True)
    parser.add_argument("--seed", type=int, default=20261016)
    parser.add_argument("--date", default="2026-10-16")
    parser.add_argument("--read-only", action="store_true")
    args = parser.parse_args()
    with psycopg.connect(database_url(), autocommit=True) as conn:
        apply_schema(conn)
        load_dataset(conn, generate_day(args.seed, args.date), args.hospital, args.read_only)
    print(f"seeded hospital '{args.hospital}' (seed {args.seed}, {args.date})")


if __name__ == "__main__":
    main()
