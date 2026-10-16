"""Agent configs are composed from safety fragments and stay in sync with the API (eng 2A/2B)."""

from __future__ import annotations

import json

import pytest

from agent.build import BUILD, FRAGMENTS, SAFETY_FRAGMENTS, build
from slotback.api.models import TOOLS


@pytest.fixture(scope="module")
def files():
    return build()


def test_committed_build_is_up_to_date(files):
    for name, text in files.items():
        assert (BUILD / name).read_text() == text, f"{name} is stale: run python -m agent.build"


def test_every_profile_contains_every_safety_rule_verbatim(files):
    for name, text in files.items():
        if name == "tools.json":
            continue
        prompt = json.loads(text)["conversation_config"]["agent"]["prompt"]["prompt"]
        for frag in SAFETY_FRAGMENTS:
            assert (FRAGMENTS / f"{frag}.md").read_text().strip() in prompt, (name, frag)


def test_first_message_discloses_ai_and_recording(files):
    for name, text in files.items():
        if name == "tools.json":
            continue
        first = json.loads(text)["conversation_config"]["agent"]["first_message"].lower()
        assert "inteligencia artificial" in first and "se graba" in first


def test_production_reference_profiles_use_zero_retention(files):
    for name, text in files.items():
        if "production-reference" in name:
            privacy = json.loads(text)["platform_settings"]["privacy"]
            assert privacy == {"record_voice": False, "zero_retention_mode": True}


def test_tool_schemas_match_api_models_and_never_take_a_patient_id(files):
    tools = {t["name"]: t for t in json.loads(files["tools.json"])}
    assert set(tools) == set(TOOLS)
    for name, t in tools.items():
        props = t["api_schema"]["request_body_schema"]["properties"]
        assert set(props) == set(TOOLS[name][0].model_fields)
        assert not {"pid", "patient_id", "patient"} & set(props)
        headers = t["api_schema"]["request_headers"]
        assert headers["X-Call-Token"] == {"variable_name": "secret__call_token"}
        assert "secret_id" in headers["X-Tool-Secret"]


def test_inbound_agents_cannot_offer_backfill(files):
    tools = json.loads(files["inbound-demo.json"])["conversation_config"]["agent"]["prompt"]
    assert "offer_backfill" not in tools["tool_names"]


def test_every_tool_parameter_has_a_description(files):
    """ElevenLabs rejects parameters without a description (found on first live push)."""
    for t in json.loads(files["tools.json"]):
        for name, prop in t["api_schema"]["request_body_schema"]["properties"].items():
            assert prop.get("description"), (t["name"], name)
