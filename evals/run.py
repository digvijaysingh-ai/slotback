"""Run the evals and write evals/results/latest.json (shown on the Evals page).

    uv run python -m evals.run --smoke      # 12-scenario smoke set (CI on agent/ changes)
    uv run python -m evals.run              # full set

Gate (D12, D21, EOV8):
  FAIL     any deterministic check fails, or the leak detector misses a planted leak
  ERRORED  a scenario could not run (e.g. ElevenLabs Tests unavailable) — not green
  PASS     everything ran and passed
Exit code 0 = PASS, 1 = FAIL, 2 = ERRORED.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo

from evals.leak import find_leaks
from evals.scenarios import SCENARIOS, SMOKE
from evals.tool_scenarios import run as run_tool
from slotback.db import apply_schema
from slotback.localdb import database_url

ROOT = Path(__file__).resolve().parents[1]


def leak_detector_report() -> dict:
    cases = json.loads((ROOT / "evals" / "known_answer" / "cases.json").read_text())
    hit = lambda c: bool(find_leaks(c["transcript"], c["verified_at"], c["context"]))  # noqa: E731
    planted = [c for c in cases if c["expect_leak"]]
    clean = [c for c in cases if not c["expect_leak"]]
    return {
        "planted": len(planted),
        "caught": sum(hit(c) for c in planted),
        "clean": len(clean),
        "false_alarms": sum(hit(c) for c in clean),
    }


def conversation_unavailable_reason() -> str | None:
    if not os.environ.get("ELEVENLABS_OUTBOUND_AGENT_ID"):
        return (
            "agent not pushed to ElevenLabs: the API key lacks the Agents permission "
            "(convai_read/convai_write)"
        )
    return None


def main(argv=None) -> int:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--only", help="comma-separated scenario ids (saves credits on reruns)")
    args = ap.parse_args(argv)
    scenarios = SMOKE if args.smoke else SCENARIOS
    if args.only:
        wanted = set(args.only.split(","))
        scenarios = [s for s in SCENARIOS if s.id in wanted]
    run_id = uuid.uuid4().hex[:8]
    base = os.environ.get("TEST_DATABASE_URL") or database_url(str(ROOT / ".data" / "pg-evals"))
    schema = f"evals_{run_id}"
    with psycopg.connect(base, autocommit=True) as c:
        c.execute(f'CREATE SCHEMA "{schema}"')
    results = []
    try:
        with psycopg.connect(
            make_conninfo(base, options=f"-csearch_path={schema}"), autocommit=True
        ) as conn:
            apply_schema(conn)
            blocked = conversation_unavailable_reason()
            convo = [s for s in scenarios if s.level == "conversation"]
            convo_results = {}
            if convo and not blocked:
                try:
                    from evals.elevenlabs_tests import run_conversation_scenarios

                    for r in run_conversation_scenarios(
                        convo,
                        os.environ["SLOTBACK_API_URL"],
                        os.environ["DEMO_ACCESS_CODE"],
                        os.environ["ELEVENLABS_API_KEY"],
                        os.environ["ELEVENLABS_INBOUND_AGENT_ID"],
                    ):
                        convo_results[r["id"]] = r
                except Exception as e:  # platform outage, quota: ERRORED, never a pass (D12)
                    blocked = f"{type(e).__name__}: {str(e)[:200]}"
            for s in scenarios:
                row = {
                    "id": s.id,
                    "persona": s.persona,
                    "language": s.language,
                    "level": s.level,
                    "checks": {},
                }
                if s.level == "tool":
                    try:
                        row["checks"] = run_tool(conn, s.id, run_id)
                        row["status"] = "pass" if all(row["checks"].values()) else "fail"
                    except Exception as e:  # a crash is a failed scenario, reported as such
                        row["status"], row["error"] = "fail", f"{type(e).__name__}: {e}"
                elif s.id in convo_results:
                    row = convo_results[s.id]
                else:
                    row["status"], row["error"] = "errored", blocked or "did not run"
                results.append(row)
    finally:
        with psycopg.connect(base, autocommit=True) as c:
            c.execute(f'DROP SCHEMA "{schema}" CASCADE')

    leak = leak_detector_report()
    counts = {
        "passed": sum(r["status"] == "pass" for r in results),
        "failed": sum(r["status"] == "fail" for r in results),
        "errored": sum(r["status"] == "errored" for r in results),
    }
    leak_ok = leak["caught"] == leak["planted"] and leak["false_alarms"] <= 2
    if counts["failed"] or not leak_ok:
        status = "FAIL"
    elif counts["errored"]:
        status = "ERRORED"
    else:
        status = "PASS"
    summary = (
        f"{counts['passed']} passed, {counts['failed']} failed, {counts['errored']} did "
        f"not run. Leak detector {leak['caught']}/{leak['planted']} caught, "
        f"{leak['false_alarms']} false alarms."
    )
    if counts["errored"]:
        summary += (
            " Not green until every scenario runs: "
            + (conversation_unavailable_reason() or "see errors")
            + "."
        )
    report = {
        "run_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "mode": "smoke" if args.smoke else "full",
        "gate": {"status": status, "summary": summary},
        "counts": counts,
        "privacy_leaks": sum(1 for r in results if r["checks"].get("nothing_disclosed") is False),
        "leak_detector": leak,
        "scenarios": results,
        "credits_used": sum(r.get("credits_used") or 0 for r in results),
        "provenance": "SIMULATED",
    }
    out = ROOT / "evals" / "results" / ("latest.json" if not args.only else "partial.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"gate {status}: {summary}")
    return {"PASS": 0, "FAIL": 1, "ERRORED": 2}[status]


if __name__ == "__main__":
    sys.exit(main())
