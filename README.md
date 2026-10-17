# Slotback

**Freed hospital appointment slots, returned to the waiting list in the hospital's order, with proof.**

A voice agent on [ElevenLabs Agents](https://elevenlabs.io/agents) calls patients a few days before a specialist appointment to confirm, cancel or move it. When a slot frees up, it calls the waiting list strictly in the order the hospital set and offers the slot. Every step is written to a signed, hash-chained ledger that anyone can verify.

This repository is the whole deployment, not just the voice demo: account research, discovery, use-case selection, business case and procurement route, solution design and DPIA, a working system, an eval gate, real phone calls, a pilot plan and an executive readout.

[![core](https://github.com/digvijaysingh-ai/slotback/actions/workflows/core.yml/badge.svg)](https://github.com/digvijaysingh-ai/slotback/actions/workflows/core.yml)
&nbsp; **[Live dashboard](https://slotback-api.onrender.com)** · **[Listen to a real call](demo/)** · **[Verify the ledger](evidence/)** · **[All documents](docs/)**

> **Fictional hospital ("Hospital General"), synthetic data only.** Every Slotback result is labelled: `SIMULATED` for the synthetic clinic day and evals, `MEASURED` only for what was actually run. Public figures are benchmarks from other Spanish regions, each with its source and year. Ground rules: [`docs/PRINCIPLES.md`](docs/PRINCIPLES.md).

![The Impact page: 14 freed slots refilled in list order on a synthetic clinic day, with the signed ledger alongside](docs/img/impact.png)

---

## The problem

Specialist no-shows in Spanish public healthcare run from **5.75%** `BENCHMARK [S5, 2024]` to **14.6%** `BENCHMARK [S6, 2011]` depending on the region. In the best-documented case, 13.8% of 400,761 appointments were missed, at about **€61** per missed visit, and **46%** of no-shows came from patients forgetting or never getting the message `BENCHMARK [S2, 2013–14]`.

Reminder calls work, but admissions staff can't make enough of them, and a slot freed the day before usually stays empty. SMS is cheaper against forgetting (our own reference study says so, and we agree), but SMS is one-way: it can't take a cancellation, and it can't hand the slot to the next person on the list.

**So Slotback doesn't sell a better reminder. It sells the loop SMS can't run:** confirm, take the cancellation, and refill the slot from the waiting list before the day, in the hospital's order.

## Why a hospital would buy it, and how

A public hospital can't pay per recovered slot it can't audit, and it can't let an AI decide who gets care first. Slotback is built around both constraints.

- **It never decides priority.** It offers a freed slot strictly in the order of the hospital's own list. That keeps it out of the EU AI Act's Annex III high-risk area (AI deciding access to public healthcare), and the ledger proves the order was followed.
- **The unit of value is the unit of price.** The hospital pays per *verified* recovered slot: refilled by the agent, attended, and matching the hospital's own booking record, minus what staff would have refilled anyway. Per-minute pricing is offered as the alternative. → [`docs/04_business_case.md`](docs/04_business_case.md)
- **It fits how Spanish public bodies buy.** A pilot under the minor-contract threshold, then an open tender, with a draft technical specification in Spanish. → [`docs/04b_tender_spec.md`](docs/04b_tender_spec.md)
- **A data protection officer can sign it off.** GDPR Art. 6.1.e and 9.2.h, a DPIA draft, and a production profile with zero retention and no recording. → [`docs/05b_dpia_draft.md`](docs/05b_dpia_draft.md)

## Hear it: real calls

Two real phone calls through Twilio to the developer's own phone, with the developer playing a synthetic patient. Annotated transcripts in Spanish and English:

| Call | What it shows |
|---|---|
| [**02 · Confirm and reschedule**](demo/calls/02-confirm-and-reschedule.md) · 2 min · [mp3](demo/calls/02-confirm-and-reschedule.mp3) | AI disclosure → identity check → reads the appointment → offers three slots → reads back → moves it in the live system → declines a medical question and books an admissions callback → hangs up itself |
| [**01 · The first real call**](demo/calls/01-first-real-call-before-fixes.md) · 3 min · [mp3](demo/calls/01-first-real-call-before-fixes.mp3) | All 15 simulated evals had passed. The first real call still found four problems: wrong-language voice, a confirm call treated as a waiting-list offer, a transfer that didn't exist, and no way to hang up. All four fixed the same day. |

## How it works

```mermaid
flowchart LR
    P((Patient)) <-- phone / browser --> EL[ElevenLabs Agent<br/>voice · LLM · tools]
    EL -- "tool webhooks<br/>X-Tool-Secret + per-call token" --> API[Slotback API<br/>FastAPI]
    EL -- "signed post-call webhook" --> API
    API --> SVC[Scheduling services<br/>identity · confirm · cancel · move<br/>backfill state machine]
    SVC --> DB[(Postgres<br/>slots · appointments<br/>waiting list · calls)]
    SVC --> L[voiceledger<br/>hash chain + signed head]
    L --> V[Verifier CLI / Verify page]
    DB --> D[Dashboard<br/>Impact · Console · ROI · Evals]
```

- **The agent can only act through tools, and the tools check everything.** Each call carries a token bound to one patient; identity is verified server-side; a tool refuses anything the call isn't allowed to do (in call 01, the server refused a waiting-list offer on a confirmation call). → [`docs/05_solution_design.md`](docs/05_solution_design.md)
- **Backfill is a state machine**, not a prompt: freed → offering (10-minute hold per rank) → filled or unfilled, with a 24-hour cut-off. Slots are freed only by a cancellation, a reschedule or staff, never by a prediction. → `slotback/domain/backfill.py`
- **The agent config is code.** Prompt fragments compose into four profiles (outbound and inbound, demo and production reference). Tool schemas are generated from the API models, and CI fails if the built config drifts. → [`agent/`](agent/)
- **Every number has a provenance.** `metrics/registry.json` tags each figure `SIMULATED`, `BENCHMARK`, `SYNTHETIC`, `MEASURED` or `ASSUMPTION`, and the docs and dashboard render it with that tag.

## Safeguards, in code

| Safeguard | Where it's enforced |
|---|---|
| AI and recording disclosed first (AI Act Art. 50) | Opening line + `record_disclosure`; eval check `ai_disclosure_first` |
| Identity before any detail (date of birth + last 3 digits and letter of the ID) | Server-side in `verify_identity`; ledger check `identity_before_detail` |
| Two failed attempts end the call; three failed calls in 24 h lock the patient | `slotback/services/scheduling.py` |
| Voicemail or a relative: callback number only | Prompt + eval scenarios `voicemail`, `relative-answers`, `wrong-number` |
| No clinical advice; a person whenever asked | `transfer_to_human`; eval scenarios `medical-question`, `wants-human`, `angry-patient` |
| Offers only in the hospital's list order | Backfill state machine; ledger check `list_order` |
| Opt-out of automated calls | `opt_out`; eval scenario `opt-out` |
| Prompt injection can't widen access | Tools act only on the patient bound to the call; eval scenario `prompt-injection` |
| Real calls only to one allow-listed number | `scripts/demo_call.py` |

## Proof: verify the ledger yourself

```bash
uv run voiceledger verify evidence/showcase-2026-10-16.zip --trusted-key $(cat evidence/trusted_key.txt) --rules voiceops.toml
```
```
PASS  1707 events
  PASS         chain: 1707 events linked
  PASS         identity_before_detail: 300 detail_disclosed events, all after identity_verified
  PASS         list_order: 14 snapshots followed in order (per slot_id)
  PASS         head: signed head matches
```

Change one event and the chain breaks at that line. → [`evidence/`](evidence/)

## Evals: a release gate, not a demo

![Release gate: 15 of 15 scenarios pass, 0 privacy leaks](docs/img/evals.png)

**Gate PASS, 15/15** `SIMULATED` (latest run 16 Oct 2026, on the current voice and LLM):

- **12 tool-level scenarios** against real Postgres, each on its own isolated hospital: social engineering, prompt injection, the two-patient race for one slot, late accept after the hold expired, lockout, voicemail, wrong number, opt-out, cancel-then-backfill in list order…
- **3 conversation scenarios on ElevenLabs Tests** against the live agent and API: an elderly patient who is hard of hearing, an angry patient, a switch to Romanian.
- **Our own deterministic checks on every transcript**, because the platform's judge is advisory: AI disclosed first, and a leak detector (es/en/ro/ar) that must catch **16/16 planted leaks with 0 false alarms** before its "0 leaks" counts.

Status is PASS, FAIL or ERRORED; a scenario that didn't run is never a pass. The tool-level scenarios run in CI on every push; the conversation scenarios run on demand because they cost credits. Results: [`evals/results/latest.json`](evals/results/latest.json) · method: [`docs/08_evals.md`](docs/08_evals.md).

**What the gate caught:** the first live run failed the angry-patient case (not offered a person); the fix was a dedicated early prompt section. **What it missed:** the four problems found by the [first real call](demo/calls/01-first-real-call-before-fixes.md). Both are logged in [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Results on one synthetic clinic day (all `SIMULATED`)

| | |
|---|---|
| Appointments / confirmation calls | 400 / 400 |
| Patients reached | 68.5% |
| Slots freed by a cancellation during the call | 14 |
| Refilled from the waiting list, in list order | 14 (median 11 min) |
| Billable after attendance and the staff baseline | 9 |
| SMS-only counterfactual | 3.7 |
| Privacy leaks found by the ledger verifier | 0 |
| Estimated cost per recovered slot | €3.54 |

The behaviour behind these numbers is **assumed, not measured**. The assumptions are listed on the dashboard and in `slotback/sim/day.py`. The [90-day pilot plan](docs/09_pilot_plan.md) is how the real values would be measured, against an SMS-only control group, with go/no-go criteria and a kill switch.

## The deployment, end to end

| Stage | Document |
|---|---|
| The story at three lengths | [`docs/00_narrative.md`](docs/00_narrative.md) |
| Account research: sizing, stakeholders, buying triggers | [`docs/01_account_brief.md`](docs/01_account_brief.md) |
| Discovery: interview guide, process map, baseline metrics | [`docs/02_discovery.md`](docs/02_discovery.md) |
| Use-case selection (six scored; triage excluded as a clinical risk) | [`docs/03_use_cases.md`](docs/03_use_cases.md) |
| Business case, pricing, procurement route | [`docs/04_business_case.md`](docs/04_business_case.md) · [tender spec (ES)](docs/04b_tender_spec.md) |
| Solution design, security, failure modes, FHIR mapping | [`docs/05_solution_design.md`](docs/05_solution_design.md) · [DPIA draft](docs/05b_dpia_draft.md) |
| Conversation design | [`docs/06_conversation_design.md`](docs/06_conversation_design.md) |
| Dashboard UX and wireframes | [`docs/07_ux.md`](docs/07_ux.md) · [`DESIGN.md`](DESIGN.md) |
| Evals | [`docs/08_evals.md`](docs/08_evals.md) |
| 90-day pilot, go/no-go, rollout | [`docs/09_pilot_plan.md`](docs/09_pilot_plan.md) |
| Operations: QA sampling, alerts, incident runbook, config rollback | [`docs/10_operations.md`](docs/10_operations.md) |
| Executive readout for the hospital director | [Spanish](readout/es/readout.md) · [English](readout/en/readout.md) · memos: [ES](readout/es/memo.md) / [EN](readout/en/memo.md) |
| Field notes to the platform's product team | [`docs/11_product_feedback.md`](docs/11_product_feedback.md) |
| Every decision, with the reason and the alternative | [`docs/DECISIONS.md`](docs/DECISIONS.md) · [design review record](docs/designs/slotback-full-build.md) |

## What's deployed

| Piece | Where |
|---|---|
| API, tool webhooks and dashboard | [slotback-api.onrender.com](https://slotback-api.onrender.com) (Render, Frankfurt; free tier, so the first load after idle takes about a minute) |
| Two agents (outbound, inbound) | ElevenLabs Agents, built and pushed from `agent/` by `voiceops build` / `voiceops push` |
| Phone line | Twilio, imported into ElevenLabs; the dialler allows one number |
| Post-call webhook | HMAC-signed, into `/hooks/post-call` |
| CI | GitHub Actions: lint, format, config drift, metrics check, 117 tests on Postgres 16, 12 tool-level eval scenarios |

The live **Try** page (browser voice session) is behind an access code to protect the call budget. The recordings in [`demo/`](demo/) show the same agent.

## Run it locally

```bash
uv sync
uv run pytest -q                          # 117 tests on real Postgres (embedded, no Docker needed)
uv run python -m slotback.serve           # http://localhost:7860, rebuilds the showcase day on boot
uv run python -m evals.run --only happy-confirm-es,race-two-patients   # tool-level evals, no credits
uv run voiceledger verify evidence/showcase-2026-10-16.zip --trusted-key $(cat evidence/trusted_key.txt) --rules voiceops.toml
```

Copy `.env.example` to `.env` for the parts that need keys (pushing agents, conversation evals, phone calls). Secrets never go in the repo.

## Repository layout

```
slotback/            FastAPI app, scheduling services, backfill state machine, dashboard, simulator
voiceops.toml        the voiceops kit's config: ledger rules, agent build, eval gate, deploy checks, call review
agent/               prompt fragments, profiles, built configs (`voiceops build`) and safety.json
evals/               scenarios, leak detector + known-answer set, ElevenLabs Tests runner, results
evidence/            the signed showcase bundle and the trusted public key
demo/                real call recordings with annotated transcripts
metrics/             every number with its provenance
docs/                the deployment documents (see the table above)
readout/             the executive readout and memo, Spanish and English
scripts/             deploy, deploy check, demo call, metrics filler, static export
db/                  schema
```

## Status and next steps

- **Done:** everything above is built, tested and deployed; two real calls recorded; eval gate green on the current agent.
- **Next:** voice-level latency (only text-test latency is measured today), calibrating the platform's judge against about 20 hand-labelled transcripts, and a real pilot, which is the only way the simulated numbers become measured ones.

## Sources

- **[S2]** Jabalera Mesa (2015), doctoral thesis, Universidad de Málaga; one Andalusian health area, data 2013–14.
- **[S5]** Galicia region, 2024 figures, press report of 28 Jan 2025.
- **[S6]** Pereira-Victorio et al. (2016), one week of Aug 2011.

Full list with links: [`research/sources.md`](research/sources.md).
