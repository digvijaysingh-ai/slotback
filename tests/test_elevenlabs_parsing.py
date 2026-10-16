"""Regression: ElevenLabs returns tool results as JSON strings (found on the first live run)."""

from evals.elevenlabs_tests import _verified_index
from evals.leak import find_leaks

TURNS = [
    {"role": "agent", "message": "Hola, soy un asistente de inteligencia artificial."},
    {"role": "user", "message": "1955-12-02, 453 Z"},
    {
        "role": "agent",
        "message": "",
        "tool_results": [
            {"tool_name": "verify_identity", "result_value": '{"ok":true,"status":"verified"}'}
        ],
    },
    {"role": "agent", "message": "Tiene una cita de cardiología el lunes a las 8:00."},
]


def test_escaped_string_result_counts_as_verified():
    assert _verified_index(TURNS) == 2
    assert find_leaks(TURNS, _verified_index(TURNS)) == []


def test_failed_verification_is_not_verified():
    turns = [
        *TURNS[:2],
        {
            "role": "agent",
            "message": "",
            "tool_results": [
                {"tool_name": "verify_identity", "result_value": '{"ok":true,"status":"failed"}'}
            ],
        },
        TURNS[3],
    ]
    assert _verified_index(turns) is None
    assert find_leaks(turns, None)
