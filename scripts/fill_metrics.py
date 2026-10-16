"""Extend metrics/registry.json and fill every {{metric:KEY}} in docs/ and readout/.

    uv run python scripts/fill_metrics.py            # update registry + fill docs
    uv run python scripts/fill_metrics.py --check    # CI: fail on unfilled or stale values

Placeholders become re-fillable markers: <!--m:KEY-->value<!--/m-->. Values come only
from the registry; anything not measured yet is written as "not yet measured", never
invented. Tool latency is MEASURED locally through the real API (embedded Postgres).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "metrics" / "registry.json"
PLACEHOLDER = re.compile(r"`?\{\{metric:([a-z0-9_]+)\}\}`?")
MARKER = re.compile(r"<!--m:([a-z0-9_]+)-->(.*?)<!--/m-->")
NOT_MEASURED = "not yet measured"


def measure_tool_latency(samples: int = 120) -> dict:
    import psycopg
    from fastapi.testclient import TestClient
    from psycopg.conninfo import make_conninfo

    from slotback.api.app import Settings, create_app
    from slotback.data.generate import generate_day
    from slotback.data.seed import load_dataset
    from slotback.db import apply_schema
    from slotback.localdb import database_url
    from slotback.services import scheduling as svc

    base = database_url(str(ROOT / ".data" / "pg-latency"))
    schema = f"lat_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(base, autocommit=True) as c:
        c.execute(f'CREATE SCHEMA "{schema}"')
    url = make_conninfo(base, options=f"-csearch_path={schema}")
    try:
        with psycopg.connect(url, autocommit=True) as conn:
            apply_schema(conn)
            load_dataset(conn, generate_day(), "live")
            rows = conn.execute(
                "SELECT a.pid, p.date_of_birth, p.id_number FROM appointments a JOIN patients p"
                " USING (hospital_id, pid) WHERE a.hospital_id = 'live' ORDER BY 1 LIMIT %s",
                (samples // 3,),
            ).fetchall()
            tokens = []
            for pid, dob, idn in rows:
                _, tok = svc.start_call(
                    conn, "live", "confirm", datetime(2026, 10, 14, 10), pid=pid
                )
                tokens.append((tok, dob.isoformat(), idn))
        settings = Settings(url, "s", "", "", "live", clock=lambda: datetime(2026, 10, 14, 10))
        times = []
        with TestClient(create_app(settings)) as client:
            h = lambda t: {"X-Tool-Secret": "s", "X-Call-Token": t}  # noqa: E731
            for tok, dob, idn in tokens:
                for name, body in [
                    (
                        "verify_identity",
                        {"date_of_birth": dob, "id_last3": idn[5:8], "id_letter": idn[-1]},
                    ),
                    ("get_appointment", {}),
                    ("confirm_appointment", {}),
                ]:
                    t0 = time.perf_counter()
                    client.post(f"/tools/{name}", json=body, headers=h(tok)).raise_for_status()
                    times.append((time.perf_counter() - t0) * 1000)
        times.sort()
        return {
            "p50": round(statistics.median(times), 1),
            "p95": round(times[int(len(times) * 0.95) - 1], 1),
            "n": len(times),
        }
    finally:
        with psycopg.connect(base, autocommit=True) as c:
            c.execute(f'DROP SCHEMA "{schema}" CASCADE')


def extend(reg: dict, latency: dict | None) -> dict:
    v = lambda k: reg.get(k, {}).get("value")  # noqa: E731
    sim = lambda val, note: {"value": val, "provenance": "SIMULATED", "note": note}  # noqa: E731
    none = lambda note: {"value": None, "provenance": "SIMULATED", "note": note}  # noqa: E731
    ev_path = ROOT / "evals" / "results" / "latest.json"
    ev = json.loads(ev_path.read_text()) if ev_path.exists() else None
    a = reg.get("assumptions", {}).get("value", {})
    filled, calls = (
        v("recovered_slots") or 0,
        (v("confirm_calls") or 0) + (v("backfill_calls") or 0),
    )
    out = dict(reg)
    out |= {
        "confirmation_rate": sim(
            round(v("confirmed") / (v("confirm_calls") * v("contact_rate")), 3)
            if v("confirmed")
            else None,
            "Confirmed ÷ patients reached",
        ),
        "early_cancellation_rate": sim(
            round(v("freed_slots") / v("confirm_calls"), 3),
            "Cancellations during the confirmation call ÷ calls",
        ),
        "voice_arm_refill_rate": sim(v("fill_rate"), "Freed slots refilled by the agent"),
        "sms_arm_refill_rate": {
            "value": a.get("staff_refill_rate"),
            "provenance": "ASSUMPTION",
            "note": "Staff refill rate assumed for the SMS-only arm",
        },
        "agent_minutes_per_recovered_slot": sim(
            round(calls * 1.5 / filled, 1) if filled else None,
            "ASSUMPTION ~1.5 billed minutes per call × calls ÷ recovered slots",
        ),
        "staff_hours_saved": sim(
            round(calls * 3 / 60, 1), "ASSUMPTION ~3 staff minutes per call avoided × calls"
        ),
        "elevenlabs_rate_per_min_usd": {
            "value": 0.08,
            "provenance": "BENCHMARK",
            "source": "ElevenLabs pricing page",
            "year": "2026",
            "note": "Extra agent minute, checked 2026-10-16",
        },
        "judge_agreement": none("Needs ~20 hand-labelled transcripts from the live agent"),
        "text_sim_turn_latency_p50_ms": none("Needs ElevenLabs Tests (agent not pushed yet)"),
        "text_sim_turn_latency_p95_ms": none("Needs ElevenLabs Tests (agent not pushed yet)"),
        "eval_task_completion": none("Conversation evals need the pushed agent"),
        "eval_tool_call_accuracy": none("Conversation evals need the pushed agent"),
        "eval_readback_rate": none("Conversation evals need the pushed agent"),
        "eval_escalation_accuracy": none("Conversation evals need the pushed agent"),
        "eval_disclosure_rate": none("Conversation evals need the pushed agent"),
    }
    if ev:
        ld = ev["leak_detector"]
        out |= {
            "eval_scenarios_total": sim(len(ev["scenarios"]), f"Scenarios in the {ev['mode']} set"),
            "eval_errored": sim(ev["counts"]["errored"], "Scenarios that could not run"),
            "leak_detector_recall": sim(
                round(ld["caught"] / ld["planted"], 3),
                f"{ld['caught']}/{ld['planted']} planted leaks caught",
            ),
            "leak_detector_false_alarms": sim(
                ld["false_alarms"], f"False alarms on {ld['clean']} clean transcripts"
            ),
        }
    if ev:
        convo = [
            r
            for r in ev["scenarios"]
            if r.get("level") == "conversation" and r["status"] in ("pass", "fail")
        ]
        if convo:
            n = len(convo)
            rate = lambda k: round(sum(r["checks"].get(k, False) for r in convo) / n, 3)  # noqa
            out |= {
                "eval_task_completion": sim(
                    rate("elevenlabs_success_condition"),
                    f"ElevenLabs Tests success condition, {n} simulated "
                    "conversations (advisory judge)",
                ),
                "eval_disclosure_rate": sim(
                    rate("ai_disclosed_first"), f"AI disclosed in the first agent turn, {n} runs"
                ),
            }
    if latency:
        out["tool_latency_p95_ms"] = {
            "value": latency["p95"],
            "provenance": "MEASURED",
            "note": f"{latency['n']} tool calls through the API on a laptop with embedded "
            f"Postgres (p50 {latency['p50']} ms); not the hosted demo",
        }
    elif "tool_latency_p95_ms" not in out:
        out["tool_latency_p95_ms"] = none("Run fill_metrics.py to measure")
    return out


def display(key: str, reg: dict) -> str:
    e = reg.get(key)
    if e is None:
        raise KeyError(key)
    val = e.get("value")
    if val is None:
        return NOT_MEASURED
    if key.endswith(("_rate", "_recall")) and isinstance(val, float) and val <= 1:
        val = f"{val:.0%}"
    elif key.endswith("_eur"):
        val = f"€{val:.2f}"
    elif key.endswith("_usd"):
        val = f"${val}"
    elif key.endswith("_ms"):
        val = f"{val} ms"
    if e["provenance"] == "MEASURED":
        return f"{val} (measured locally)"
    return str(val)


def fill_text(text: str, reg: dict) -> str:
    text = PLACEHOLDER.sub(
        lambda m: f"<!--m:{m.group(1)}-->{display(m.group(1), reg)}<!--/m-->", text
    )
    return MARKER.sub(lambda m: f"<!--m:{m.group(1)}-->{display(m.group(1), reg)}<!--/m-->", text)


def files():
    return sorted([*ROOT.glob("docs/**/*.md"), *ROOT.glob("readout/**/*.md")])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--no-latency", action="store_true")
    args = ap.parse_args()
    reg = json.loads(REG.read_text())
    if args.check:
        bad = []
        for f in files():
            t = f.read_text()
            if PLACEHOLDER.search(t) or fill_text(t, reg) != t:
                bad.append(str(f.relative_to(ROOT)))
        if bad:
            print("unfilled or stale metrics (run scripts/fill_metrics.py):", bad)
            return 1
        print("metrics filled and current")
        return 0
    latency = None if args.no_latency else measure_tool_latency()
    reg = extend(reg, latency)
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    n = 0
    for f in files():
        t = f.read_text()
        new = fill_text(t, reg)
        if new != t:
            f.write_text(new)
            n += 1
    print(
        f"registry: {len(reg)} entries; filled {n} files"
        + (f"; tool p95 {latency['p95']} ms (local)" if latency else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
