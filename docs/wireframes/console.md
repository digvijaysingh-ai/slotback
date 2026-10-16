# Wireframe · Console

**Purpose:** the admissions team's day-to-day view: who is being called, what needs a human, which slots are being refilled, and the kill switch.
**Primary user:** head of admissions and admissions staff.

## Desktop (≥1024 px)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Fictional hospital · synthetic data · simulated results are labelled                  [EN|ES]│
├────────────┬───────────────────────────────────────────────────────┬─────────────────────────┤
│ SLOTBACK   │ Console · today                    [ Pause all calling ]│ FREED SLOTS             │
│            │                                     (danger, code)      │ CAR-07 ✓ filled r2      │
│   Impact   │ PATIENTS REACHED  <!--m:contact_rate-->68%<!--/m--> [SIMULATED]   │ DER-03 ⟳ offering r1    │
│ ▸ Console  │ ─────────────────────────────────────────────────────── │        hold 07:42 left  │
│   Calls    │ CALL BOARD                                               │ OPH-11 ✕ unfilled       │
│   ROI      │ Status        Patient ref  Time   Flow        Markers    │        (out of time)    │
│   Evals    │ ⟳ calling     P-0213       10:02  confirm                │ ─────────────────────── │
│   Verify   │ ◆ verified    P-0187       10:01  backfill    ◆ID ◆AI    │ COST PER RECOVERED SLOT │
│   Try      │ ✓ confirmed   P-0152       09:58  confirm     ◆ID ◆RB    │ € ▯▯ (m1)               │
│            │ ✓ cancelled   P-0098       09:55  confirm     ◆ID ◆RB    │ [SIMULATED]             │
│            │ ○ voicemail   P-0077       09:54  confirm     callback # │ rate ▯▯ /min (m2)       │
│            │ ◆ handed over P-0031       09:50  confirm     ◆human     │ [rate, date checked]    │
│            │ ─────────────────────────────────────────────────────── │                         │
│            │ EXCEPTIONS (needs a human)                               │ ─────────────────────── │
│            │ P-0031  asked a clinical question    [ Call back ]       │ ALERTS                  │
│            │ P-0144  3 failed identity calls 🔒    [ Review ]          │ ✓ privacy flags: none   │
│            │ P-0201  wrong number reported        [ Review ]          │ ✓ webhook errors < 5%   │
│            │                                                         │ ⟳ tool p95 ▯▯ ms (m3)   │
│            │                                                         │                         │
│            │                                                         │ ✓ transfers normal      │
└────────────┴───────────────────────────────────────────────────────┴─────────────────────────┘
 ◆ID identity verified · ◆AI AI disclosed · ◆RB read back · ◆human handed to a human
```

Placeholders: (m1) <!--m:cost_per_recovered_slot_eur-->€3.54<!--/m--> · (m2) <!--m:elevenlabs_rate_per_min_usd-->$0.08<!--/m--> · (m3) <!--m:tool_latency_p95_ms-->0.9 ms (measured locally)<!--/m-->.

Patient references (`P-0213`) are synthetic IDs. The board shows no names and no specialty until identity is verified; unverified rows show "—" for flow details.

**Actions (all need the access code, all logged, D17):** Pause all calling (kill switch), Start a demo campaign, Call back, Review. The kill switch banner when active: "Calling paused by {{user}} at {{time}}. [Resume]".

**The four alerts (D24):** privacy flag, transfer spike, webhook error rate > 5%, tool p95 > 300 ms.

## Phone (<768 px)

Read-only: patients reached, count of exceptions, "Calling paused" banner if active. No actions.

## States

| State | What shows |
|---|---|
| Loading | Skeleton rows |
| Empty board | "No calls scheduled today. Next campaign: Mon 09:00." + "Start a demo campaign" (access code) |
| Empty exceptions | "Nothing needs a human right now." |
| Error | Row-level error with retry; webhook-error alert in the rail |
| Success | Live rows, polled every 3 s from the shared board cache; polling pauses on hidden tabs |
| Partial | "Calling paused (kill switch)" banner with who and when |

## Copy notes

- "Patients reached", never "calls dialled".
- The cost meter is SIMULATED wherever minutes are simulated; its rate and the date the rate was checked come from the registry.
- The lockout icon 🔒 is always paired with text ("3 failed identity calls").
