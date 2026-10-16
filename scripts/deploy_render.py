"""Deploy (or update) the live API on Render as a free Docker web service.

    uv run python scripts/deploy_render.py            # create or update, then wait for live

Uses RENDER_API_KEY from .env. Secrets are sent as environment variables and never
printed. The service builds from the GitHub repo's Dockerfile; autodeploy on push.
Approved 2026-10-16 (public URL for ElevenLabs tool webhooks).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
NAME = "slotback-api"
REPO = "https://github.com/digvijaysingh-ai/slotback"
ENV_KEYS = [
    "TOOL_SECRET",
    "DEMO_ACCESS_CODE",
    "ELEVENLABS_WEBHOOK_SECRET",
    "ELEVENLABS_INBOUND_AGENT_ID",
]


def main() -> int:
    load_dotenv(ROOT / ".env")
    c = httpx.Client(
        base_url="https://api.render.com/v1",
        timeout=60,
        headers={
            "Authorization": f"Bearer {os.environ['RENDER_API_KEY']}",
            "Accept": "application/json",
        },
    )
    owner = c.get("/owners", params={"limit": 1}).json()[0]["owner"]["id"]
    env = [{"key": k, "value": os.environ[k]} for k in ENV_KEYS if os.environ.get(k)]
    env.append({"key": "PORT", "value": "7860"})
    existing = [s["service"] for s in c.get("/services", params={"name": NAME}).json()]
    if existing:
        svc = existing[0]
        r = c.put(f"/services/{svc['id']}/env-vars", json=env)
        if r.status_code >= 400:
            raise SystemExit(f"env update failed: {r.status_code} {r.text[:300]}")
        c.post(f"/services/{svc['id']}/deploys", json={}).raise_for_status()
    else:
        r = c.post(
            "/services",
            json={
                "type": "web_service",
                "name": NAME,
                "ownerId": owner,
                "repo": REPO,
                "branch": "main",
                "autoDeploy": "yes",
                "envVars": env,
                "serviceDetails": {
                    "runtime": "docker",
                    "plan": "free",
                    "region": "frankfurt",
                    "healthCheckPath": "/health",
                    "envSpecificDetails": {"dockerfilePath": "./Dockerfile", "dockerContext": "."},
                },
            },
        )
        if r.status_code >= 400:
            raise SystemExit(f"create failed: {r.status_code} {r.text[:500]}")
        svc = r.json()["service"]
    url = svc["serviceDetails"]["url"]
    print(f"service {svc['id']} · {url} · waiting for deploy…", flush=True)
    for _ in range(90):  # up to ~15 min (first Docker build on the free plan is slow)
        dep = c.get(f"/services/{svc['id']}/deploys", params={"limit": 1}).json()[0]["deploy"]
        if dep["status"] == "live":
            print(f"live: {url}")
            return 0
        if dep["status"] in ("build_failed", "update_failed", "canceled", "deactivated"):
            print(f"deploy {dep['status']} — see the Render dashboard logs")
            return 1
        time.sleep(10)
    print("still deploying; check the Render dashboard")
    return 2


if __name__ == "__main__":
    sys.exit(main())
