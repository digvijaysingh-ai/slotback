# Wireframe · ROI

**Purpose:** let a director (or a reviewer) see the break-even point and the cost per recovered slot, and change every input, each with its provenance.
**Primary user:** hospital director and finance; the deployment lead in a sales meeting.

## Desktop (≥1024 px)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Fictional hospital · synthetic data · simulated results are labelled                  [EN|ES]│
├────────────┬───────────────────────────────────────────────────────┬─────────────────────────┤
│ SLOTBACK   │ ROI · pilot specialty                                   │ SENSITIVITY             │
│            │ BREAK-EVEN                    € PER RECOVERED SLOT       │ What moves break-even   │
│   Impact   │ ▯▯▯ recovered slots / month   € ▯▯ (m1)                  │ most (tornado, ±range)  │
│   Console  │ [SIMULATED]                   [SIMULATED]                │ fill rate      ████████ │
│   Calls    │                                                          │ contact rate   ██████   │
│ ▸ ROI      │ ─────────────────────────────────────────────────────── │ cost / missed  █████    │
│   Evals    │ INPUTS                                                   │ € per minute   ██       │
│   Verify   │ Appointments / year  ──●──── 380,000        [SYNTHETIC]  │ SMS cost       █        │
│   Try      │ No-show rate         ──●──── 12%            [SYNTHETIC]  │                         │
│            │   range shown 5.75%–14.6%          [BENCHMARK S5/S6]     │ bars drawn from the     │
│            │ Cost per missed appt ──●──── €61   [BENCHMARK S2, 2013–14]│ formula in 04; no      │
│            │ Patients reachable   ──●──── ▯▯   [ASSUMPTION]           │ values in wireframe     │
│            │ Early-cancel rate    ──●──── ▯▯   [SIMULATED]            │                         │
│            │ Backfill fill rate   ──●──── ▯▯   [SIMULATED]            │ PRICING                 │
│            │ Agent minutes / call ──●──── ▯▯   [SIMULATED]            │ ( ) per minute          │
│            │ € per agent minute   ──●──── ▯▯   [rate, date checked]   │ ( ) per completed call  │
│            │ SMS cost             ──●──── ▯▯   [ASSUMPTION]           │ (●) per recovered slot  │
│            │ SMS-arm refill rate  ──●──── ▯▯   [SIMULATED]            │ ( ) hybrid              │
│            │                                                         │ → see 04_business_case  │
│            │ [ Reset to defaults ]                                    │                         │
└────────────┴───────────────────────────────────────────────────────┴─────────────────────────┘
```

(m1) is <!--m:cost_per_recovered_slot_eur-->€3.54<!--/m-->. `▯▯` marks a value read from `metrics/registry.json` or from the default inputs in `04_business_case.md`. `ASSUMPTION` is not one of the four D28 tags; inputs a visitor sets themselves show `ASSUMPTION` until changed, then `USER INPUT`. *(Open: confirm with the dashboard lane whether these two extra tags are allowed or whether such inputs reuse `SYNTHETIC`.)*

## Phone (<768 px)

Read-only: break-even and € per recovered slot with defaults, plus "Open on a larger screen to change inputs".

## States

| State | What shows |
|---|---|
| Loading | n/a (client-side calculation) |
| Empty | Never empty: prefilled with defaults |
| Error | Invalid input shown inline next to the slider ("Enter a rate between 0% and 100%") |
| Success | Live recalculation as sliders move |

## Copy notes

- Every slider has a tag, and the hover names the source or says "assumption, change me".
- The formulas are the ones in `04_business_case.md`; the page links to them.
- The billable definition is one click away: filled by the agent AND attended AND matched to the hospital's booking, minus the SMS-arm baseline.
