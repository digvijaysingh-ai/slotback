# Wireframe · Call detail

**Purpose:** show exactly what happened on one call: outcome, safeguards, transcript, tool calls and ledger events, side by side.
**Primary user:** admissions staff handling an exception; the DPO or QA lead reviewing a sample; a reviewer checking "is it careful?".

## Desktop (≥1024 px)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Fictional hospital · synthetic data · simulated results are labelled                  [EN|ES]│
├────────────┬───────────────────────────────────────────────────────┬─────────────────────────┤
│ SLOTBACK   │ ← Calls   Call conv_7f2…a91 · P-0187 · backfill          │ LEDGER EVENTS           │
│            │ OUTCOME  ✓ filled CAR-07       FLAGS  privacy: none ✓    │ #0412 ◆ ai_disclosed    │
│   Impact   │                                       escalation: none   │ #0413 ◆ identity_ok     │
│   Console  │ ◆ AI disclosed  ◆ identity verified  ◆ read back          │ #0417 offer r2  CAR-07  │
│ ▸ Calls    │ ─────────────────────────────────────────────────────── │ #0418 ◆ read_back       │
│   ROI      │ TRANSCRIPT (ES · EN gloss)        │ TOOL CALLS            │ #0419 ✓ filled  CAR-07  │
│   Evals    │ 00:00 Agent  «Buenos días. Le     │                       │                         │
│   Verify   │   llamo del Hospital General. Soy │                       │ trace id = conversation │
│   Try      │   un asistente automático…»       │                       │ id (D24)                │
│            │   ◆ AI disclosed                  │                       │ ─────────────────────── │
│            │   gloss: "…I'm an automated…"     │                       │ AUDIO (demo calls only) │
│            │ 00:14 Agent  «¿Me dice su fecha   │                       │ ▶ ──●──────── 01:52     │
│            │   de nacimiento?»                 │                       │ recorded under the demo │
│            │ 00:21 Patient «[DOB redacted]»    │ verify_identity       │ profile                 │
│            │                                   │  → verified ✓ ▯ ms*   │                         │
│            │   ◆ identity verified             │                       │                         │
│            │ 00:30 Agent  «Se ha liberado una  │ offer_backfill        │                         │
│            │   cita de cardiología…»           │  → hold 10 min        │                         │
│            │ 00:48 Agent  «Entonces: el martes │                       │                         │
│            │   … ¿es correcto?»  ◆ read back   │                       │                         │
│            │ 00:52 Patient «Sí.»               │ accept_backfill       │                         │
│            │                                   │  → filled ✓           │                         │
└────────────┴───────────────────────────────────────────────────────┴─────────────────────────┘
 * per-call latencies are shown from the trace; wireframe values are positional only.
```

Identity factors are redacted in the transcript view (`[DOB redacted]`, `[ID redacted]`). Specialty appears in the transcript only after the ◆ identity verified marker, matching what the agent was allowed to say.

## Phone (<768 px)

Read-only: outcome, flags, and the transcript as a single column. No audio, no actions.

## States

| State | What shows |
|---|---|
| Loading | Skeleton |
| Empty | "This call has no transcript (voicemail / no answer)." + the ledger events that exist |
| Error | "Call not found" + back |
| Success | Full view |
| Partial | "Transcript still processing" note (post-call webhook not yet received) |

## Copy notes

- Flags are words, not just colours: "privacy: none ✓", "privacy: flagged ✕ — see line 00:21".
- Audio exists only for demo-profile calls to the developer's own phone; production-reference calls are not recorded.
- The tool-call column shows the tool name, result and server latency; never the raw payload.
