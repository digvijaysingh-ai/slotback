"""Every dashboard page renders, carries provenance tags, and keeps actions gated (eng 3A).

These are server-side render tests; the Playwright smoke suite runs the same pages in a
browser against the deployed Space (scripts/deploy_check.py).
"""

from __future__ import annotations

import uuid
from datetime import datetime

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from slotback.api.app import Settings, create_app
from slotback.serve import boot

PAGES = [
    "/",
    "/impact",
    "/console",
    "/console?h=live",
    "/roi",
    "/evals",
    "/verify",
    "/try",
    "/?lang=es",
    "/impact?lang=es",
]


@pytest.fixture(scope="module")
def client(pg_url):
    schema = f"t_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(pg_url, autocommit=True) as c:
        c.execute(f'CREATE SCHEMA "{schema}"')
    url = make_conninfo(pg_url, options=f"-csearch_path={schema}")
    boot(url, "live")
    settings = Settings(url, "s", "h", "code", "live", clock=lambda: datetime(2026, 10, 14, 10))
    with TestClient(create_app(settings)) as c:
        yield c
    with psycopg.connect(pg_url, autocommit=True) as c:
        c.execute(f'DROP SCHEMA "{schema}" CASCADE')


@pytest.mark.parametrize("path", PAGES)
def test_page_renders(client, path):
    r = client.get(path)
    assert r.status_code == 200, r.text[:500]
    assert "Fictional hospital" in r.text or "Hospital ficticio" in r.text


def test_simulated_numbers_are_tagged(client):
    for path in ["/", "/impact", "/console"]:
        assert 'class="tag sim"' in client.get(path).text, path


def test_specialty_hidden_until_verified(client):
    html = client.get("/console?h=showcase&status=no_answer").text
    assert "Cardiology" not in html.split("<tbody>")[1].split("</tbody>")[0]


def test_tamper_demo_breaks_a_copy_only(client):
    r = client.post("/api/demo/tamper", json={"seq": 5}).json()
    assert r["ok"] is False and r["checks"]["chain"]["seq"] == 5
    assert "✓ Verified" in client.get("/impact?lang=en").text


def test_actions_need_the_access_code(client):
    assert (
        client.post("/api/kill-switch", params={"access_code": "x", "paused": True}).status_code
        == 403
    )
    assert client.post("/api/sessions", json={"access_code": "x"}).status_code == 403


def test_evidence_route_does_not_escape_its_folder(client):
    assert client.get("/evidence/..%2F.env").status_code == 404
    assert client.get("/evidence/showcase-2026-10-16.zip").status_code == 200
