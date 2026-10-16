# Demo: real calls

Real phone calls placed by the Slotback outbound agent on ElevenLabs Agents, through Twilio, to the developer's own phone. The dialler (`scripts/demo_call.py`) refuses any number except one allow-listed in the environment.

The person answering is the developer **playing a synthetic patient**: the date of birth and ID digits come from the generated test data (the ID deliberately fails the Spanish DNI checksum). The hospital is fictional. Each call opens with Twilio's trial-account notice, which is not part of the agent.

| | Call | Length | What to listen for |
|---|---|---|---|
| ▶ | [**02 · Confirm and reschedule**](calls/02-confirm-and-reschedule.md) · [mp3](calls/02-confirm-and-reschedule.mp3) | 2:06 | The full flow working: disclosure, identity, read the appointment, offer three slots, read back, move it, decline a medical question, book a callback, hang up |
| ▶ | [**01 · The first real call**](calls/01-first-real-call-before-fixes.md) · [mp3](calls/01-first-real-call-before-fixes.mp3) | 3:09 | Four problems simulations didn't catch, and the server-side guard that held anyway |

## Between the two calls

1. **Read the transcript and tool log of call 01** line by line, and found four root causes (table in the call 01 page).
2. **Fixed them in code and config**, not by retrying: `call_purpose` from `verify_identity`, `callback_requested` from `transfer_to_human`, the `end_call` tool, a native Spain-Spanish voice, a pinned LLM, telephone audio format, and spare slots in the live demo day so a patient can actually move an appointment.
3. **Rehearsed on ElevenLabs Tests** before ringing a phone again: a simulated patient ran the same confirm-and-reschedule flow against the live API. The first rehearsal failed (no free slots to move to); the second passed.
4. **Re-ran the full eval gate** on the new voice and LLM: PASS 15/15.
5. **Placed call 02**, then reviewed it the same way. One more flaw (an invented "email confirmation") was fixed in the prompt afterwards.

Every step is logged in [`docs/DECISIONS.md`](../docs/DECISIONS.md).

## Place a call yourself

```bash
uv run python scripts/demo_call.py setup          # import your Twilio number into ElevenLabs
uv run python scripts/demo_call.py call           # rings DEMO_PHONE_ALLOWLIST; prints the synthetic patient's details
uv run python scripts/demo_call.py fetch CONV_ID  # saves the recording and transcript locally
```

Needs `ELEVENLABS_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `DEMO_PHONE_ALLOWLIST` and `DEMO_ACCESS_CODE` in `.env`.
