"""Tool request models: the single source of truth for tool schemas (eng 2B).

`agent/build.py` generates the ElevenLabs webhook-tool definitions from TOOLS, and
CI fails if the committed definitions drift from these models.
No model has a patient id field: tools act on the patient bound to the call token.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Empty(BaseModel):
    pass


class VerifyIdentity(BaseModel):
    date_of_birth: str = Field(
        description="Patient's date of birth as YYYY-MM-DD.", pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    id_last3: str = Field(
        description="Last three digits of the patient's ID number.", pattern=r"^\d{3}$"
    )
    id_letter: str = Field(
        description="The letter at the end of the patient's ID number.", pattern=r"^[A-Za-z]$"
    )


class CancelAppointment(BaseModel):
    patient_confirmed: bool = Field(
        description="True only after you read the appointment back and the patient said "
        "an explicit yes to cancelling it."
    )


class Reschedule(BaseModel):
    slot_id: str = Field(
        description="A slot_id returned by list_alternative_slots. Never invent one.",
        max_length=40,
    )


class TransferToHuman(BaseModel):
    reason: str = Field(
        description="Short reason, e.g. 'medical question', 'asked for a person'.",
        max_length=200,
    )


class LogOutcome(BaseModel):
    outcome: Literal[
        "confirmed",
        "cancelled",
        "rescheduled",
        "voicemail",
        "third_party",
        "wrong_number",
        "transferred",
        "opted_out",
        "no_decision",
        "backfill_booked",
        "backfill_declined",
    ] = Field(description="How the call ended. Pick the closest value.")


# name -> (request model, description shown to the agent)
TOOLS: dict[str, tuple[type[BaseModel], str]] = {
    "record_disclosure": (
        Empty,
        "Call right after you have said you are an AI assistant and that the call is recorded.",
    ),
    "verify_identity": (
        VerifyIdentity,
        "Check the patient's identity. Say nothing about any appointment until this returns "
        "status 'verified'.",
    ),
    "get_appointment": (Empty, "Get the verified patient's next appointment."),
    "confirm_appointment": (Empty, "Confirm the appointment after reading it back."),
    "cancel_appointment": (
        CancelAppointment,
        "Cancel the appointment. Requires an explicit yes after the read-back.",
    ),
    "list_alternative_slots": (Empty, "List real open slots for rescheduling."),
    "reschedule": (Reschedule, "Move the appointment to a slot from list_alternative_slots."),
    "offer_backfill": (
        Empty,
        "Backfill calls only: get the freed slot to offer and start the 10-minute hold.",
    ),
    "accept_backfill": (
        Empty,
        "Backfill calls only: book the offered slot after the patient says yes.",
    ),
    "decline_backfill": (Empty, "Backfill calls only: the patient does not want the slot."),
    "transfer_to_human": (TransferToHuman, "Hand the call to admissions staff."),
    "opt_out": (Empty, "The verified patient does not want automated calls any more."),
    "log_outcome": (LogOutcome, "Record how the call ended, just before ending it."),
}
