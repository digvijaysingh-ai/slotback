# Wireframe · Evals

**Purpose:** show whether the current agent version passes the release gate, which scenarios fail and why, and how it compares with the previous version.
**Primary user:** a reviewer; the hospital's QA lead; the DPO (privacy row).

## Desktop (≥1024 px)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Fictional hospital · synthetic data · simulated results are labelled                  [EN|ES]│
├────────────┬───────────────────────────────────────────────────────┬─────────────────────────┤
│ SLOTBACK   │ Evals · agent config {{version}} · run {{run_id}}       │ LEAK DETECTOR           │
│            │ GATE  ✓ PASS / ✕ FAIL / ⟳ ERRORED        [SIMULATED]    │ known-answer set        │
│   Impact   │ privacy leaks ▯ (m1)  (gate: 0)                          │ recall ▯ (m2)           │
│   Console  │ ─────────────────────────────────────────────────────── │   (gate: 100%)          │
│   Calls    │ SCENARIO × PERSONA          cells: ✓ pass ✕ fail ⟳ err   │ false alarms ▯ (m3)     │
│   ROI      │              conf canc resch backf vm  3rd hand opt      │   (gate: ≤2)            │
│ ▸ Evals    │ baseline      ●    ●    ●     ●     ·   ·   ·    ●       │ ─────────────────────── │
│   Verify   │ elderly HoH   ●    ●    ●     ●     ·   ·   ●    ·       │ METRICS     [SIMULATED] │
│   Try      │ interrupter   ●    ●    ●     ●     ·   ·   ·    ·       │ task completion ▯ (m4)  │
│            │ relative      ●    ·    ·     ●     ·   ●   ·    ·       │ tool calls ▯ (m5)       │
│            │ voicemail     ●    ·    ·     ●     ●   ·   ·    ·       │ escalation ▯ (m6)       │
│            │ wrong number  ●    ·    ·     ●     ·   ●   ·    ·       │ disclosure ▯ (m7)       │
│            │ angry         ●    ●    ·     ●     ·   ·   ●    ·       │ read-back ▯ (m8)        │
│            │ medical q.    ●    ●    ·     ●     ·   ·   ●    ·       │ text-sim turn latency   │
│            │ wants human   ●    ·    ●     ●     ·   ·   ●    ·       │   p95 ▯ ms (m9)         │
│            │ lang RO/AR    ●    ·    ·     ●     ·   ·   ●    ·       │ ERRORED ▯ (m10)         │
│            │ soc. engineer ●    ·    ·     ●     ·   ●   ·    ·       │                         │
│            │ injection     ●    ●    ·     ●     ·   ·   ·    ·       │                         │
│            │ accept→change ·    ·    ·     ●     ·   ·   ·    ·       │                         │
│            │ race (2 acc.) ·    ·    ·     ●     ·   ·   ·    ·       │                         │
│            │ ● in suite (shows ✓/✕/⟳ after a run) · not in suite      │                         │
│            │ ─────────────────────────────────────────────────────── │ ─────────────────────── │
│            │ ADVISORY (ElevenLabs built-in evaluation, tone)           │ VS PREVIOUS VERSION     │
│            │ not part of the gate                                     │ regressions: list       │
└────────────┴───────────────────────────────────────────────────────┴─────────────────────────┘
```

Placeholders: (m1) <!--m:privacy_leaks-->0<!--/m--> · (m2) <!--m:leak_detector_recall-->100%<!--/m--> · (m3) <!--m:leak_detector_false_alarms-->0<!--/m--> · (m4) <!--m:eval_task_completion-->1.0<!--/m--> · (m5) <!--m:eval_tool_call_accuracy-->not yet measured<!--/m--> · (m6) <!--m:eval_escalation_accuracy-->not yet measured<!--/m--> · (m7) <!--m:eval_disclosure_rate-->100%<!--/m--> · (m8) <!--m:eval_readback_rate-->not yet measured<!--/m--> · (m9) <!--m:text_sim_turn_latency_p95_ms-->not yet measured<!--/m--> · (m10) <!--m:eval_errored-->0<!--/m-->.

The ● cells mirror the suite matrix in `08_evals.md`; after a run each shows ✓ / ✕ / ⟳ from the results. Clicking a cell opens the transcript in Call detail.

## Phone (<768 px)

Read-only: gate status, privacy leaks, ERRORED count.

## States

| State | What shows |
|---|---|
| Loading | Skeleton matrix |
| Empty | "No eval run yet. Run the smoke suite." |
| Error | "Run failed" with a link to the CI log |
| Success | PASS banner |
| Partial | Amber banner: "3 of 12 scenarios ERRORED — gate not green" |

## Copy notes

- Every result on this page is `SIMULATED` (text tests, not real calls).
- Latency is labelled "text-sim turn latency", never "voice latency".
- The advisory tone score is visually separated from the gate and labelled "advisory".
