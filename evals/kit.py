"""Slotback's hooks for the voiceops gate: scenarios, tool runner, conversation setup.

    uv run voiceops gate --smoke           # smoke set
    uv run voiceops gate --level tool      # deterministic, no credits (CI)
    uv run voiceops gate                   # full set; conversation level spends credits

The gate itself (PASS / FAIL / ERRORED, leak detector known answers, the ElevenLabs Tests
adapter, results JSON) is the kit's; what's here is Slotback's domain.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import psycopg
from psycopg.conninfo import make_conninfo
from voiceops.evals import ConversationSetup, ConversationUnavailable, Scenario

from evals import scenarios as _scenarios
from evals.tool_scenarios import run as run_tool
from slotback.data.generate import generate_day
from slotback.db import apply_schema
from slotback.localdb import database_url

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = [Scenario(**asdict(s)) for s in _scenarios.SCENARIOS]


def live_patient(seed: int = 20261016) -> dict:
    """The live hospital is seeded with clinic day = server's today + 3 (slotback.serve)."""
    clinic = (datetime.now(UTC).date() + timedelta(days=3)).isoformat()
    ds = generate_day(seed, clinic)
    appt = sorted(ds.appointments, key=lambda a: a.appointment_id)[0]
    p = next(x for x in ds.patients if x.pid == appt.pid)
    return {
        "dob": p.date_of_birth,
        "last3": p.id_number[5:8],
        "letter": p.id_number[-1],
        "name": p.given_name,
    }


@contextmanager
def tool_runner(run_id: str):
    """Each run gets its own schema; each scenario its own hospital (EOV5)."""
    base = os.environ.get("TEST_DATABASE_URL") or database_url(str(ROOT / ".data" / "pg-evals"))
    schema = f"evals_{run_id}"
    with psycopg.connect(base, autocommit=True) as c:
        c.execute(f'CREATE SCHEMA "{schema}"')
    try:
        with psycopg.connect(
            make_conninfo(base, options=f"-csearch_path={schema}"), autocommit=True
        ) as conn:
            apply_schema(conn)
            yield lambda scenario_id: run_tool(conn, scenario_id, run_id)
    finally:
        with psycopg.connect(base, autocommit=True) as c:
            c.execute(f'DROP SCHEMA "{schema}" CASCADE')


def conversation(cfg) -> ConversationSetup:
    """Fresh widget-style sessions on the live API; a simulated patient with real
    synthetic credentials; the inbound demo agent."""
    if not os.environ.get("ELEVENLABS_OUTBOUND_AGENT_ID"):
        raise ConversationUnavailable(
            "agent not pushed to ElevenLabs: the API key lacks the Agents permission "
            "(convai_read/convai_write)"
        )
    api = httpx.Client(base_url=os.environ["SLOTBACK_API_URL"], timeout=90)
    api.get("/health")  # wake a sleeping free instance
    pat = live_patient()

    def new_session(s):
        sess = api.post("/api/sessions", json={"access_code": os.environ["DEMO_ACCESS_CODE"]})
        sess = sess.json()
        return {"secret__call_token": sess["call_token"], "call_id": sess["call_id"]}

    def persona(s):
        return (
            f"{s.prompt} You are a synthetic test patient calling Hospital General "
            f"about your specialist appointment. When asked, your date of birth is "
            f"{pat['dob']}, the last three digits of your ID are {pat['last3']} and "
            f"the letter is {pat['letter']}. You want to confirm the appointment."
        )

    return ConversationSetup(
        api_key=os.environ["ELEVENLABS_API_KEY"],
        agent_id=os.environ["ELEVENLABS_INBOUND_AGENT_ID"],
        new_session=new_session,
        persona=persona,
        disclosure_markers=("inteligencia artificial", "ai assistant", "artificial"),
        context="patient",
        name_prefix="slotback-eval",
        raw_out=ROOT / "evals" / "results" / "elevenlabs_raw.json",
    )


def call_instructions() -> str:
    p = live_patient()
    return (
        "You are the synthetic patient. When the agent asks:\n"
        f"  date of birth: {p['dob']}   last 3 ID digits: {p['last3']}   letter: {p['letter']}\n"
        "Then confirm, reschedule or cancel."
    )
