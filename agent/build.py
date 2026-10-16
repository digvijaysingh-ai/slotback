"""Compose agent configs from prompt fragments + profiles, and tool schemas from the API models.

    uv run python -m agent.build           # (re)write agent/build/*.json
    uv run python -m agent.build --check   # CI: fail if committed JSON is stale (eng 2A/2B)

Output is deterministic and committed, so every prompt or tool change shows up as a
reviewable diff. Deployment-specific values stay as placeholders filled by push.py:
{{TOOL_BASE_URL}} and {{TOOL_SECRET_ID}}.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import get_args

from slotback.api.models import TOOLS

ROOT = Path(__file__).resolve().parent
FRAGMENTS = ROOT / "fragments"
BUILD = ROOT / "build"
SAFETY_FRAGMENTS = (
    "10_disclosure",
    "20_identity",
    "30_privacy",
    "40_clinical",
    "70_human_and_optout",
)
FIRST_MESSAGE = {
    "outbound": "Hola, le llamo del Hospital General. Soy un asistente de inteligencia "
    "artificial y esta llamada se graba. Llamo por una cita: ¿hablo con la persona "
    "titular de la cita?",
    "inbound": "Hola, Hospital General. Soy un asistente de inteligencia artificial y esta "
    "llamada se graba. ¿En qué puedo ayudarle?",
}
# Native Spain-Spanish voice (peninsular): the default English voice mangled Spanish on the
# first phone call. LLM pinned: the platform default drifted to a model we never chose.
VOICE_ID = "UOIqAnmS11Reiei1Ytkc"  # "Carolina", ElevenLabs voice library, es / peninsular
LLM = "claude-haiku-4-5"
OUTBOUND_ONLY_TOOLS = {"offer_backfill", "accept_backfill", "decline_backfill"}


def _property(schema: dict) -> dict:
    out = {"description": schema.get("description", "")}
    if "enum" in schema or "const" in schema:
        out |= {"type": "string", "enum": schema.get("enum") or [schema["const"]]}
    else:
        out["type"] = {"boolean": "boolean", "integer": "integer"}.get(schema.get("type"), "string")
    return out


def tool_schema(name: str) -> dict:
    model, description = TOOLS[name]
    js = model.model_json_schema()
    props = {k: _property(v) for k, v in js.get("properties", {}).items()}
    for field_name, field in model.model_fields.items():  # Literal -> enum
        args = get_args(field.annotation)
        if args and all(isinstance(a, str) for a in args):
            props[field_name] = {
                "type": "string",
                "enum": list(args),
                "description": field.description or "",
            }
    return {
        "type": "webhook",
        "name": name,
        "description": description,
        "response_timeout_secs": 10,
        "api_schema": {
            "url": "{{TOOL_BASE_URL}}/tools/" + name,
            "method": "POST",
            "request_headers": {
                "X-Tool-Secret": {"secret_id": "{{TOOL_SECRET_ID}}"},
                "X-Call-Token": {"variable_name": "secret__call_token"},
            },
            "request_body_schema": {
                "type": "object",
                "description": description,
                "properties": props,
                "required": sorted(js.get("required", [])),
            },
        },
    }


def compose_prompt(fragments: list[str]) -> str:
    return "\n\n".join((FRAGMENTS / f"{f}.md").read_text().strip() for f in fragments) + "\n"


def build() -> dict[str, str]:
    profiles = json.loads((ROOT / "profiles.json").read_text())
    files: dict[str, str] = {}
    files["tools.json"] = json.dumps(
        [tool_schema(n) for n in TOOLS], indent=2, ensure_ascii=False, sort_keys=True
    )
    for key, p in profiles.items():
        if key.startswith("_"):
            continue
        missing = [f for f in SAFETY_FRAGMENTS if f not in p["fragments"]]
        if missing:
            raise SystemExit(f"profile {key} is missing safety fragments: {missing}")
        tools = [n for n in TOOLS if p["direction"] == "outbound" or n not in OUTBOUND_ONLY_TOOLS]
        config = {
            "name": p["name"],
            "conversation_config": {
                "agent": {
                    "first_message": FIRST_MESSAGE[p["direction"]],
                    "language": "es",
                    "prompt": {
                        "llm": LLM,
                        "temperature": 0.2,
                        "prompt": compose_prompt(p["fragments"]),
                        "tool_names": tools,
                        # The agent hangs up itself after the goodbye (first phone call
                        # looped on goodbyes until the patient hung up).
                        "built_in_tools": {
                            "end_call": {
                                "name": "end_call",
                                "description": "End the call after log_outcome and goodbye.",
                                "params": {"system_tool_type": "end_call"},
                            }
                        },
                    },
                },
                "tts": {
                    "model_id": "eleven_flash_v2_5",
                    "voice_id": VOICE_ID,
                    # Phone agents speak the telephone codec natively (no resampling on Twilio).
                    **(
                        {"agent_output_audio_format": "ulaw_8000"}
                        if p["direction"] == "outbound"
                        else {}
                    ),
                },
                **(
                    {"asr": {"user_input_audio_format": "ulaw_8000"}}
                    if p["direction"] == "outbound"
                    else {}
                ),
            },
            "platform_settings": {
                "privacy": {
                    "record_voice": p["record_voice"],
                    "zero_retention_mode": p["zero_retention_mode"],
                }
            },
        }
        files[f"{key}.json"] = json.dumps(config, indent=2, ensure_ascii=False, sort_keys=True)
    return {name: text + "\n" for name, text in files.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = build()
    if args.check:
        stale = [
            n for n, t in files.items() if not (BUILD / n).exists() or (BUILD / n).read_text() != t
        ]
        if stale:
            print(f"stale agent build files (run `python -m agent.build`): {stale}")
            return 1
        print("agent build up to date")
        return 0
    BUILD.mkdir(exist_ok=True)
    for name, text in files.items():
        (BUILD / name).write_text(text)
    print(f"wrote {len(files)} files to {BUILD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
