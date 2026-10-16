# Wireframe · Verify

**Purpose:** let anyone check a day's ledger bundle against its signed head, without trusting the app that produced it.
**Primary user:** a reviewer (after downloading the bundle from Impact); in production, the hospital's auditor or DPO.

## Desktop (≥1024 px)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Fictional hospital · synthetic data · simulated results are labelled                  [EN|ES]│
├────────────┬───────────────────────────────────────────────────────┬─────────────────────────┤
│ SLOTBACK   │ Verify a ledger bundle                                  │ WHAT EACH CHECK PROVES  │
│            │ ┌───────────────────────────────────────────────────┐ │                         │
│   Impact   │ │   Drop a bundle (.zip, max 5 MB) here               │ │ Hash chain: no event    │
│   Console  │ │   or [ Choose file ]    [ Try the sample bundle ]   │ │ was changed, removed or │
│   Calls    │ └───────────────────────────────────────────────────┘ │ reordered.              │
│   ROI      │ access code required for uploads                        │                         │
│   Evals    │ ─────────────────────────────────────────────────────── │ Signed head: the last   │
│ ▸ Verify   │ RESULT  bundle 2026-…-showcase.zip                       │ hash matches the head   │
│   Try      │ ✓ hash chain        ▯▯▯▯ events linked*                 │ the hospital received.  │
│            │ ✓ signed head       Ed25519, key id k1                   │                         │
│            │ ✓ list order        every offer followed list rank       │ List order: every offer │
│            │ ✓ identity first    no detail before ◆ identity_ok       │ went to the next rank.  │
│            │                                                         │                         │
│            │ On failure:                                              │ Identity first: no      │
│            │ ✕ hash chain        broken at #0417 (event changed)      │ appointment detail      │
│            │                                                         │ before verification.    │
│            │ Also available offline:                                  │                         │
│            │ $ slotback verify bundle.zip                             │ What it does NOT prove: │
│            │                                                         │ that a fill really      │
│            │                                                         │ happened. Billing is    │
│            │                                                         │ checked against the     │
│            │                                                         │ hospital's own booking  │
│            │                                                         │ record.                 │
└────────────┴───────────────────────────────────────────────────────┴─────────────────────────┘
 * event count comes from the bundle; the figure shown is the wireframe's example only.
```

## Phone (<768 px)

Read-only: the verify status of the showcase bundle ("✓ verified, head signed") and the plain-language list of what each check proves. No uploads.

## States

| State | What shows |
|---|---|
| Loading | "Checking N events…" progress |
| Empty | Drop zone with "Try the sample bundle" |
| Error | Specific: "Not a Slotback bundle" / "File over 5 MB" / "Too many uploads, try again in a minute" |
| Success | Green checks per invariant |
| Partial | Ledger-only upload: "List order: not checked (no snapshots)" |

## Copy notes

- Uploads are schema-validated, never executed or rendered as HTML, rate-limited to 10/min per IP, and behind the access code.
- The "does NOT prove" box is mandatory (OV2): the ledger is tamper-evident evidence; the hospital's booking system is the source of truth.
