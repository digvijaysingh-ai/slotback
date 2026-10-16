# Wireframe · Impact

**Purpose:** show the outcome of one synthetic clinic day, replay how it happened, and prove the ledger is tamper-evident.
**Primary user:** hospital director; a first-time visitor in their first minute.
**Opens on:** the **end state** of the showcase day (answer first), with "Replay the day ▶" available.

## Desktop (≥1024 px)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Fictional hospital · synthetic data · simulated results are labelled                  [EN|ES]│
├────────────┬───────────────────────────────────────────────────────┬─────────────────────────┤
│ SLOTBACK   │ Impact · showcase day (SYNTHETIC)                       │ LEDGER        ✓ verified│
│            │                                                         │ head: 3f9a…c21 (signed) │
│ ▸ Impact   │ <!--m:recovered_slots-->14<!--/m-->    <!--m:fill_rate-->100%<!--/m-->      │ ─────────────────────── │
│   Console  │ recovered slots               of freed slots refilled   │ #0412 ◆ ai_disclosed    │
│   Calls    │ [SIMULATED]                   [SIMULATED]               │ #0413 ◆ identity_ok     │
│   ROI      │                                                         │ #0414 slot_freed  CAR-07│
│   Evals    │ vs SMS-only <!--m:sms_arm_refill_rate-->35%<!--/m--> [SIMULATED]  │ #0415 offer r1    CAR-07│
│   Verify   │ median time to fill <!--m:median_time_to_fill_min-->11.0<!--/m-->  │ #0416 no_answer r1      │
│   Try      │ min [SIMULATED]                                         │ #0417 offer r2    CAR-07│
│            │ ───────────────────────────────────────────────────────│ #0418 ◆ read_back       │
│            │ DAY TIMELINE  08:00 ──────────────────────── 18:00      │ #0419 ✓ filled    CAR-07│
│            │ cardiology     ✓ ✓ ⟳ ✓ ✕                                │ #0420 ◆ identity_ok     │
│            │ dermatology    ✓ ✓                                      │ ...                     │
│            │ orthopaedics   ✓ ⟳ ✓                                    │                         │
│            │ ophthalmology  ✓ ✕                                      │ [ Tamper with one event ]│
│            │ gastroent.     ✓ ✓ ✓                                    │   (danger outline)      │
│            │  ✓ filled  ⟳ offering  ✕ unfilled                       │ [ Download bundle ]     │
│            │                                                         │ → Verify it yourself    │
│            │ [ Replay the day ▶ ]  ◀◀ ‖ ▶▶  ──●──────── scrub        │                         │
│            │ 5 specialties · 400 appointments · 60 per list [SYNTHETIC]│                       │
└────────────┴───────────────────────────────────────────────────────┴─────────────────────────┘
```

Markers in the timeline are positions only (wireframe); real positions come from the showcase bundle.

**Replay:** 60 s; markers step freed → offering r1/r2 → filled; counter climbs; ledger lines appear in sync. Pausable and scrubbable by keyboard. With reduced motion, it steps without animating.

**Tamper:** edits one event in an in-memory copy. The ledger header turns ✕ "chain broken at #0417", the row is outlined in `--unfilled`, and a "Restore" button appears. Nothing is written to the database.

## Phone (<768 px)

Read-only: headline number + tag, replay as a vertical event list, verify status ("✓ verified, head signed"), "Watch the 3-minute video". No tamper on phones.

## States

| State | What shows |
|---|---|
| Loading | Skeleton timeline |
| Empty | "No slots were freed today. Freed slots appear here as patients cancel." + "Replay a past day" |
| Error | "Couldn't load the ledger" + retry |
| Success | End state with verified chain |
| Partial | Amber banner: "Head not signed — verification limited" |

## Copy notes

- "Recovered slots" here means fills recorded in the ledger in the simulated day. The billable definition (attended + matched to the hospital booking − SMS-arm baseline) is shown on hover with a link to `04_business_case.md`: <!--m:billable_recovered_slots-->9<!--/m--> [SIMULATED].
- Slot IDs like `CAR-07` are synthetic labels. No patient names appear on this page.
