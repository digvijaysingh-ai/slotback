# Wireframe · Try

**Purpose:** let a visitor with the access code talk to the agent in the browser as a synthetic patient, and watch the tools fire live.
**Primary user:** a reviewer; a director in a meeting.

## Desktop (≥1024 px)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Fictional hospital · synthetic data · simulated results are labelled                  [EN|ES]│
├────────────┬───────────────────────────────────────────────────────┬─────────────────────────┤
│ SLOTBACK   │ Try it · talk to the agent                              │ LIVE TOOL CALLS         │
│            │ Access code [________]  [ Start ]                       │ 00:21 verify_identity   │
│   Impact   │ ─────────────────────────────────────────────────────── │   → verified ✓          │
│   Console  │ 1. Pick a persona            2. Pick a scenario         │   token bound           │
│   Calls    │ (●) Carmen Ruiz (SYNTHETIC)  (●) confirm                │ 00:30 get_appointment   │
│   ROI      │     72, hearing difficulty   ( ) cancel                 │   → ok                  │
│   Evals    │ ( ) Andrei Pop (SYNTHETIC)   ( ) backfill offer         │ 00:48 confirm_          │
│   Verify   │     RO speaker               ( ) ask a medical question │   appointment → ✓       │
│ ▸ Try      │ ( ) Test patient (SYNTHETIC) ( ) ask for a human        │                         │
│            │                                                         │ ◆ AI disclosed          │
│            │ YOUR CARD (say these when asked)                         │ ◆ identity verified     │
│            │ DOB 03/02/1954 · ID last 3 + letter: 417-K               │ ◆ read back             │
│            │ (synthetic; the ID fails the DNI checksum)               │                         │
│            │ ─────────────────────────────────────────────────────── │ LEDGER                  │
│            │ [ ● Start talking ]   session 00:52 / 3:00               │ #0901 ◆ ai_disclosed    │
│            │ (ElevenLabs widget)                                      │ #0902 ◆ identity_ok     │
│            │                                                         │ #0903 ✓ confirmed       │
└────────────┴───────────────────────────────────────────────────────┴─────────────────────────┘
```

The persona card gives the visitor the synthetic identity factors to say. Widget sessions start **unbound** and bind on `verify_identity` (1C); widget dynamic variables are set by the browser and are not trusted.

## Phone (<768 px)

No sessions on phones. Shows "Watch the 3-minute video" instead.

## States

| State | What shows |
|---|---|
| Loading | "Connecting…" |
| Empty | Access code prompt |
| Error | "Monthly demo minutes used up. Watch the recording." / "Wrong access code" |
| Success | Live session with the tool-call feed |
| Partial | Warning at 2:30: "30 seconds left in this demo session" |

## Copy notes

- Sessions are capped at 3 minutes to protect the monthly minute budget.
- Each session runs in its own hospital ID so it can't touch the showcase day.
- The synthetic persona details shown here are the only identity factors the visitor ever sees.
