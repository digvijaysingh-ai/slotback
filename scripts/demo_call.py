"""Bonus demo: the outbound agent phones the developer's OWN number through Twilio.

    uv run python scripts/demo_call.py setup          # import the Twilio number into ElevenLabs
    uv run python scripts/demo_call.py call           # place one call; prints what to say
    uv run python scripts/demo_call.py fetch CONV_ID  # save recording + transcript to recordings/

The only number that can ever be dialled is DEMO_PHONE_ALLOWLIST (E.164, one number).
The call is a confirm call bound to a synthetic patient of the live hospital: you play
that patient, so you must give the synthetic date of birth and ID digits printed here.
Secrets come from .env and are never printed. Recordings stay local (gitignored).
API shapes: elevenlabs.io/docs/api-reference (phone-numbers, twilio/outbound-call,
conversations), checked 2026-10-16.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
STATE = ROOT / "agent" / "state.json"
OUT = ROOT / "recordings"
E164 = re.compile(r"^\+[1-9]\d{6,14}$")


def env(key: str) -> str:
    v = os.environ.get(key, "").strip()
    if not v:
        raise SystemExit(f"{key} is missing in .env")
    return v


def allowed_number() -> str:
    nums = [n.strip() for n in env("DEMO_PHONE_ALLOWLIST").split(",") if n.strip()]
    if len(nums) != 1 or not E164.match(nums[0]):
        raise SystemExit("DEMO_PHONE_ALLOWLIST must be exactly one E.164 number, e.g. +34600000000")
    return nums[0]


def el() -> httpx.Client:
    return httpx.Client(
        base_url="https://api.elevenlabs.io",
        headers={"xi-api-key": env("ELEVENLABS_API_KEY")},
        timeout=60,
    )


def load_state() -> dict:
    return json.loads(STATE.read_text())


def setup() -> int:
    state = load_state()
    from_number = env("TWILIO_FROM_NUMBER")
    with el() as c:
        r = c.get("/v1/convai/phone-numbers")
        r.raise_for_status()
        existing = [p for p in r.json() if p.get("phone_number") == from_number]
        if existing:
            pn_id = existing[0]["phone_number_id"]
        else:
            r = c.post(
                "/v1/convai/phone-numbers",
                json={
                    "provider": "twilio",
                    "phone_number": from_number,
                    "label": "Slotback demo (developer's own phone only)",
                    "sid": env("TWILIO_ACCOUNT_SID"),
                    "token": env("TWILIO_AUTH_TOKEN"),
                },
            )
            if r.status_code >= 400:
                raise SystemExit(f"import failed: {r.status_code} {r.text[:300]}")
            pn_id = r.json()["phone_number_id"]
        # Calls go out through the outbound agent; nothing inbound is routed to this number.
        state["phone_number_id"] = pn_id
        STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Twilio number imported into ElevenLabs: {pn_id}")
    return 0


def call() -> int:
    from evals.elevenlabs_tests import live_patient

    to = allowed_number()
    state = load_state()
    if "phone_number_id" not in state:
        raise SystemExit("run `setup` first")
    api = env("SLOTBACK_API_URL").rstrip("/")
    with httpx.Client(base_url=api, timeout=90) as a:
        a.get("/health")  # wake the free instance
        r = a.post(
            "/api/sessions",
            json={"access_code": env("DEMO_ACCESS_CODE"), "purpose": "confirm"},
        )
        r.raise_for_status()
        sess = r.json()
    with el() as c:
        r = c.post(
            "/v1/convai/twilio/outbound-call",
            json={
                "agent_id": state["agents"]["outbound-demo"],
                "agent_phone_number_id": state["phone_number_id"],
                "to_number": to,
                "conversation_initiation_client_data": {
                    "dynamic_variables": {
                        "secret__call_token": sess["call_token"],
                        "call_id": sess["call_id"],
                    }
                },
            },
        )
        if r.status_code >= 400:
            raise SystemExit(f"call failed: {r.status_code} {r.text[:300]}")
        body = r.json()
    p = live_patient()
    print(f"Calling your allow-listed number ending …{to[-3:]}")
    print(f"conversation_id: {body.get('conversation_id')}")
    print("You are the synthetic patient. When the agent asks:")
    print(f"  date of birth: {p['dob']}   last 3 ID digits: {p['last3']}   letter: {p['letter']}")
    print("Then confirm, reschedule or cancel. Afterwards: demo_call.py fetch <conversation_id>")
    return 0


def fetch(conv_id: str) -> int:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", conv_id):
        raise SystemExit("bad conversation id")
    OUT.mkdir(exist_ok=True)
    with el() as c:
        r = c.get(f"/v1/convai/conversations/{conv_id}")
        r.raise_for_status()
        conv = r.json()
        turns = [
            {"role": t.get("role"), "message": t.get("message")}
            for t in conv.get("transcript") or []
            if t.get("message")
        ]
        (OUT / f"{conv_id}.json").write_text(json.dumps(turns, indent=1, ensure_ascii=False))
        r = c.get(f"/v1/convai/conversations/{conv_id}/audio")
        if r.status_code < 400:
            (OUT / f"{conv_id}.mp3").write_bytes(r.content)
    print(f"status: {conv.get('status')} · {len(turns)} turns → recordings/{conv_id}.json/.mp3")
    for t in turns:
        print(f"  {t['role']}: {t['message']}")
    return 0


def main() -> int:
    load_dotenv(ROOT / ".env")
    args = sys.argv[1:]
    if args == ["setup"]:
        return setup()
    if args == ["call"]:
        return call()
    if len(args) == 2 and args[0] == "fetch":
        return fetch(args[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
