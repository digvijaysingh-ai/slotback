"""Push the built agent configs to ElevenLabs (create or update), idempotently.

    uv run python -m agent.push --base-url https://<api-host> --profile inbound-demo

Prerequisites (checked first, nothing is half-written):
  - ELEVENLABS_API_KEY with the Agents permission (convai_read + convai_write)
  - TOOL_SECRET (stored in ElevenLabs as a workspace secret, sent as X-Tool-Secret)
  - --base-url: a public HTTPS URL of the API that passed scripts/deploy_check.py

IDs are written to agent/state.json (not secret). Endpoint shapes follow the ElevenLabs
API reference as of 2026-10-16; this script has not yet run against the live API
because the key lacked the Agents permission (docs/OPEN_QUESTIONS.md).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
API = "https://api.elevenlabs.io"
STATE = ROOT / "state.json"
SECRET_NAME = "slotback_tool_secret"


def fill(obj, base_url: str, secret_id: str):
    text = json.dumps(obj)
    return json.loads(
        text.replace("{{TOOL_BASE_URL}}", base_url.rstrip("/")).replace(
            "{{TOOL_SECRET_ID}}", secret_id
        )
    )


def preflight(client: httpx.Client) -> str | None:
    r = client.get("/v1/convai/agents", params={"page_size": 1})
    if r.status_code == 401 and "convai" in r.text:
        return "API key lacks the Agents permission (convai_read/convai_write)"
    if r.status_code >= 400:
        return f"ElevenLabs API error {r.status_code}: {r.text[:120]}"
    return None


def main(argv=None) -> int:
    load_dotenv(ROOT.parent / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--profile", default="inbound-demo")
    ap.add_argument("--dry-run", action="store_true", help="print the payloads, call nothing")
    args = ap.parse_args(argv)
    key, tool_secret = os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("TOOL_SECRET")
    if not key or not tool_secret:
        print("ELEVENLABS_API_KEY and TOOL_SECRET must be set")
        return 2
    tools = json.loads((ROOT / "build" / "tools.json").read_text())
    agent = json.loads((ROOT / "build" / f"{args.profile}.json").read_text())
    state = json.loads(STATE.read_text()) if STATE.exists() else {"tools": {}, "agents": {}}
    if args.dry_run:
        print(
            json.dumps(
                fill({"tools": tools, "agent": agent}, args.base_url, "<secret_id>"),
                indent=2,
                ensure_ascii=False,
            )[:4000]
        )
        return 0
    with httpx.Client(base_url=API, headers={"xi-api-key": key}, timeout=60) as c:
        problem = preflight(c)
        if problem:
            print(f"not pushing: {problem}")
            return 2

        def ok(r: httpx.Response) -> httpx.Response:
            if r.status_code >= 400:
                raise SystemExit(
                    f"{r.request.method} {r.request.url.path} -> {r.status_code}: {r.text[:600]}"
                )
            return r

        def save() -> None:  # after every step, so a failure never orphans what was created
            STATE.write_text(json.dumps(state, indent=2) + "\n")

        if "secret_id" not in state:  # reuse an existing secret with our name
            existing = ok(c.get("/v1/convai/secrets")).json().get("secrets", [])
            match = [s for s in existing if s.get("name") == SECRET_NAME]
            if match:
                state["secret_id"] = match[0]["secret_id"]
            else:
                r = ok(
                    c.post(
                        "/v1/convai/secrets",
                        json={"type": "new", "name": SECRET_NAME, "value": tool_secret},
                    )
                )
                state["secret_id"] = r.json()["secret_id"]
            save()
        remote = {}  # name -> [ids] of tools already in the workspace
        for t in ok(c.get("/v1/convai/tools")).json().get("tools", []):
            remote.setdefault(t["tool_config"]["name"], []).append(t["id"])
        tool_ids = {}
        for tool in fill(tools, args.base_url, state["secret_id"]):
            name = tool["name"]
            known = state["tools"].get(name) or (remote.get(name) or [None])[0]
            for dup in [i for i in remote.get(name, []) if i != known]:
                ok(c.delete(f"/v1/convai/tools/{dup}"))  # clean up duplicates from failed runs
            if known:
                ok(c.patch(f"/v1/convai/tools/{known}", json={"tool_config": tool}))
                state["tools"][name] = known
            else:
                r = ok(c.post("/v1/convai/tools", json={"tool_config": tool}))
                state["tools"][name] = r.json()["id"]
            tool_ids[name] = state["tools"][name]
            save()
        prompt = agent["conversation_config"]["agent"]["prompt"]
        prompt["tool_ids"] = [tool_ids[n] for n in prompt.pop("tool_names")]
        if args.profile in state["agents"]:
            ok(c.patch(f"/v1/convai/agents/{state['agents'][args.profile]}", json=agent))
        else:
            r = ok(c.post("/v1/convai/agents/create", json=agent))
            state["agents"][args.profile] = r.json()["agent_id"]
        save()
    print(f"pushed {args.profile}: agent {state['agents'][args.profile]}, {len(tool_ids)} tools")
    return 0


if __name__ == "__main__":
    sys.exit(main())
