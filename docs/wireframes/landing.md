# Wireframe · Landing

**Purpose:** orient a first-time visitor in five seconds and send them to the Impact page.
**Primary user:** a visitor evaluating the project; secondarily a hospital director following a link.
**Layout:** one composition, max width 1280 px. No left rail, no grid of boxes.

## Desktop (≥1024 px)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Fictional hospital · synthetic data · simulated results are labelled  [EN|ES]│ ← context bar
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SLOTBACK                                                                    │
│                                                                              │
│  ▯▯ (m1)                                    vs  ▯▯ (m2)                      │
│  freed slots refilled, SMS + voice              freed slots refilled, SMS only│
│  [SIMULATED]                                    [SIMULATED]                  │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  A voice agent that calls patients before their specialist appointment,      │
│  and offers any freed slot to the next person on the hospital's own list.    │
│                                                                              │
│  [ See the live day → ]        Read the case study                           │
│     (primary button)           (secondary link)                              │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────── │
│  Why: 13.8% of appointments missed in one health area   [BENCHMARK S2, 2013–14]│
│       29.6% of non-attenders said they forgot            [BENCHMARK S2, 2013–14]│
│                                                                              │
│  ◆ AI disclosed on every call  ◆ identity before detail  ◆ human on request  │
└──────────────────────────────────────────────────────────────────────────────┘
```

Placeholders: (m1) <!--m:voice_arm_refill_rate-->100%<!--/m--> · (m2) <!--m:sms_arm_refill_rate-->35%<!--/m-->. Below them, a smaller line: <!--m:recovered_slots-->14<!--/m--> slots returned to the waiting list in the showcase day [SIMULATED].

## Phone (<768 px)

Single column: context bar → headline number with tag → one sentence → "See the live day →" → "Watch the 3-minute video". Same content, stacked.

## States

| State | What shows |
|---|---|
| Loading (Space waking) | "Waking the demo (up to 30 s)" with a progress bar |
| Error | "The demo server didn't start. Retry · Watch the recorded demo" |
| Success | As above |
| Empty / partial | n/a: values always come from the committed showcase bundle |

## Copy notes

- The headline is a comparison, not a boast. Both numbers carry `SIMULATED`.
- Benchmarks name their source ID and year; the hover shows the full source from `research/sources.md`.
- No vendor claims, no "revolutionary", no stock imagery.
