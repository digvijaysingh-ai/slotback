"""Seeding into real Postgres."""

from __future__ import annotations

import pytest

from slotback.data.generate import generate_day
from slotback.data.seed import HospitalExists, load_dataset


def counts(conn, hospital_id):
    q = "SELECT count(*) FROM {} WHERE hospital_id = %s"
    return {
        table: conn.execute(q.format(table), (hospital_id,)).fetchone()[0]
        for table in ("patients", "slots", "appointments", "waitlist_entries")
    }


def test_seed_loads_one_clinic_day(pg):
    ds = generate_day()
    load_dataset(pg, ds, "showcase", read_only=True)
    assert counts(pg, "showcase") == {
        "patients": len(ds.patients),
        "slots": 400,
        "appointments": 400,
        "waitlist_entries": len(ds.waitlist),
    }
    assert (
        pg.execute("SELECT read_only FROM hospitals WHERE hospital_id = 'showcase'").fetchone()[0]
        is True
    )


def test_hospitals_are_isolated(pg):
    load_dataset(pg, generate_day(1), "eval-run-a")
    load_dataset(pg, generate_day(2), "eval-run-b")
    assert counts(pg, "eval-run-a")["slots"] == counts(pg, "eval-run-b")["slots"] == 400


def test_refuses_to_overwrite_a_hospital(pg):
    load_dataset(pg, generate_day(), "showcase")
    with pytest.raises(HospitalExists):
        load_dataset(pg, generate_day(), "showcase")
    assert counts(pg, "showcase")["slots"] == 400


def test_waitlist_rank_is_unique_per_specialty(pg):
    load_dataset(pg, generate_day(), "h")
    dupes = pg.execute(
        "SELECT specialty, rank, count(*) FROM waitlist_entries"
        " WHERE hospital_id = 'h' GROUP BY 1, 2 HAVING count(*) > 1"
    ).fetchall()
    assert dupes == []
