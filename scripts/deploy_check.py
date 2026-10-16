"""Post-deploy check (D26): run after every deploy and before pushing the agent config.

    uv run python scripts/deploy_check.py http://localhost:7860
    uv run python scripts/deploy_check.py https://<host>          # hosted API

Checks: health and seeded hospitals · tool call without the secret is rejected · signed
tool call works · the showcase bundle verifies on /api/verify · every page renders ·
tool p95 within the 300 ms budget. Exit 0 only if everything passes.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["/", "/impact", "/console", "/roi", "/evals", "/verify", "/try"]
BUDGET_MS = 300


def main(base: str) -> int:
    load_dotenv(ROOT / ".env")
    secret = os.environ.get("TOOL_SECRET", "")
    code = os.environ.get("DEMO_ACCESS_CODE", "")
    results: list[tuple[str, bool, str]] = []
    with httpx.Client(base_url=base.rstrip("/"), timeout=30) as c:
        r = c.get("/health")
        results.append(
            ("health", r.status_code == 200 and r.json().get("hospitals", 0) >= 2, r.text[:80])
        )
        r = c.post("/tools/get_appointment", json={}, headers={"X-Call-Token": "x"})
        results.append(("unsigned tool call rejected", r.status_code == 401, str(r.status_code)))
        times = []
        if code:
            tok = c.post("/api/sessions", json={"access_code": code}).json()["call_token"]
            for _ in range(20):
                t0 = time.perf_counter()
                r = c.post(
                    "/tools/get_appointment",
                    json={},
                    headers={"X-Tool-Secret": secret, "X-Call-Token": tok},
                )
                times.append((time.perf_counter() - t0) * 1000)
            ok = r.status_code == 200 and r.json().get("error") == "identity_not_verified"
            results.append(("signed tool call (unbound token refused detail)", ok, r.text[:80]))
        else:
            results.append(("signed tool call", False, "DEMO_ACCESS_CODE not set"))
        bundle = (ROOT / "evidence" / "showcase-2026-10-16.zip").read_bytes()
        key = (ROOT / "evidence" / "trusted_key.txt").read_text().strip()
        r = c.post("/api/verify", params={"trusted_key": key}, files={"file": ("b.zip", bundle)})
        results.append(
            (
                "showcase bundle verifies",
                r.status_code == 200 and r.json()["ok"],
                str(r.json().get("checks", {}).get("head", {}).get("detail", ""))[:60],
            )
        )
        bad = [p for p in PAGES if c.get(p).status_code != 200]
        results.append(("all pages render", not bad, ",".join(bad) or "8 pages"))
        if times:
            times.sort()
            p95 = times[int(len(times) * 0.95) - 1]
            results.append(
                (
                    f"tool round trip p95 ≤ {BUDGET_MS} ms (client-side)",
                    p95 <= BUDGET_MS,
                    f"{p95:.0f} ms",
                )
            )
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({detail})")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:7860"))
