"""Real Postgres for tests (no SQLite, eng review 1A).

CI sets DATABASE_URL to a Postgres service container. Locally, without
DATABASE_URL, we start an embedded server via `pgserver` (pip-installed
Postgres binaries, no Docker needed). Each test gets a fresh schema.
"""

from __future__ import annotations

import os
import uuid

import psycopg
import pytest

from slotback.db import apply_schema


@pytest.fixture(scope="session")
def pg_url(tmp_path_factory):
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("CI_DATABASE_URL")
    if url:
        yield url
        return
    pgserver = pytest.importorskip("pgserver")
    server = pgserver.get_server(tmp_path_factory.mktemp("pg"), cleanup_mode="stop")
    yield server.get_uri()


@pytest.fixture
def pg(pg_url):
    """A connection whose search_path points at a brand-new schema with our tables."""
    schema = f"t_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(pg_url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{schema}"')
        conn.execute(f'SET search_path TO "{schema}"')
        apply_schema(conn)
        try:
            yield conn
        finally:
            conn.execute(f'DROP SCHEMA "{schema}" CASCADE')
