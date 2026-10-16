"""Postgres access. DATABASE_URL comes from the environment (.env locally, secrets in CI/Space)."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from slotledger import pg as ledger_pg

SCHEMA_SQL = Path(__file__).resolve().parent.parent / "db" / "schema.sql"


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set (see .env.example)")
    return url


def apply_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA_SQL.read_text())
    ledger_pg.apply_schema(conn)
