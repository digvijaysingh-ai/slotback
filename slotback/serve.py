"""Entrypoint for the Space and local runs.

    uv run python -m slotback.serve        # http://localhost:7860

On boot (fresh container, embedded Postgres):
  1. start Postgres (DATABASE_URL if set, else embedded pgserver),
  2. rebuild the read-only showcase day with the simulator (deterministic, ~1 s),
  3. seed a writable "live" hospital whose clinic day is 3 days ahead,
  4. serve the API and dashboard.
A failure in any step exits non-zero, so the Space health check fails loudly (D14)
instead of serving a half-seeded database.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import date, timedelta

import psycopg
import uvicorn
from dotenv import load_dotenv

from slotback.api.app import Settings, create_app, madrid_now
from slotback.data.generate import generate_day
from slotback.data.seed import load_dataset
from slotback.db import apply_schema
from slotback.localdb import database_url
from slotback.sim.day import simulate_day


def boot(url: str, live_hospital: str) -> None:
    with psycopg.connect(url, autocommit=True) as conn:
        apply_schema(conn)
        if not conn.execute("SELECT 1 FROM hospitals WHERE hospital_id = 'showcase'").fetchone():
            simulate_day(conn, "showcase", 20261016, "2026-10-16")
            conn.execute("UPDATE hospitals SET read_only = true WHERE hospital_id = 'showcase'")
        row = conn.execute(
            "SELECT clinic_date FROM hospitals WHERE hospital_id = %s", (live_hospital,)
        ).fetchone()
        if row is None or row[0] <= madrid_now().date():
            if row is not None:
                conn.execute("DELETE FROM hospitals WHERE hospital_id = %s", (live_hospital,))
            clinic = (date.today() + timedelta(days=3)).isoformat()
            ds = generate_day(20261016, clinic)
            load_dataset(conn, ds, live_hospital)
            add_spare_capacity(conn, live_hospital, clinic, sorted({x.specialty for x in ds.slots}))


SPARE_TIMES = ("09:00", "11:30", "13:00")


def add_spare_capacity(conn, hospital_id: str, clinic: str, specialties: list[str]) -> None:
    """Open slots on the two days after the clinic day, so a patient can actually move an
    appointment (a fully booked day left `list_alternative_slots` empty on a real call)."""
    rows = []
    for offset in (1, 2):
        day = date.fromisoformat(clinic) + timedelta(days=offset)
        for spec in specialties:
            for t in SPARE_TIMES:
                sid = f"S-{spec[:3].upper()}-9-{day:%m%d}-{t.replace(':', '')}"
                rows.append((hospital_id, sid, spec, 9, f"{day}T{t}:00", 15))
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO slots (hospital_id, slot_id, specialty, room, starts_at, minutes, status)"
            " VALUES (%s, %s, %s, %s, %s, %s, 'unfilled') ON CONFLICT DO NOTHING",
            rows,
        )


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    url = database_url()
    os.environ["DATABASE_URL"] = url
    os.environ.setdefault("TOOL_SECRET", os.environ.get("TOOL_SECRET") or "")
    if not os.environ["TOOL_SECRET"]:
        sys.exit("TOOL_SECRET is not set")
    settings = Settings.from_env()
    boot(url, settings.live_hospital)
    uvicorn.run(
        create_app(settings),
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7860)),
        log_level="warning",
    )


if __name__ == "__main__":
    main()
