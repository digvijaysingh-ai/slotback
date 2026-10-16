---
status: ACTIVE
---
# Slotback — design and review decisions

This record holds every scope, engineering and design decision for Slotback with its code (D, E, OV, ENG, EOV, T); `docs/DECISIONS.md` logs later decisions made during the build.

Date: 2026-10-16 | Mode: scope expansion
Repo: github.com/digvijaysingh-ai/slotback
Base design: the earlier approved design doc (superseded wherever it conflicts with this file; see EOV7)

## Vision

### 10x Check
Turn the demo into **a deployment kit a Spanish public health service could actually procure**. The kit has four parts:
- the working agent;
- the tender specification the buyer would publish;
- the privacy impact assessment (DPIA) the data protection officer signs;
- the integration standard IT expects (FHIR R4).

The **Backfill Ledger** ties them together. It is a **tamper-evident** recovered-slot record. Each day's head hash is signed and handed to the hospital: in the demo, an Ed25519-signed `head.json` stored outside the app database. Once the hospital holds the head, an auditor can check that the record wasn't rewritten afterwards. In the vendor pages we found (CallSphere, Simba Voice, Ethon, IntelePeer; search of 2026-10-16), fill rates are quoted with no stated method or audit trail.

### Platonic Ideal
A visitor opens one URL:
1. Within 60 seconds they watch a synthetic clinic day replay. A slot frees up, the agent calls the next patient in list order, and the patient accepts.
2. The ledger turns green, and a SIMULATED cost-per-recovered-slot meter ticks.
3. They press "tamper". The hash chain breaks on screen, and the verifier names the broken event.
4. They upload the day's export bundle to the standalone verifier and see it pass against the signed head.
5. They open a Spanish tender spec that pays per verified recovered slot, and a DPIA draft the data protection officer could sign.

The feeling: "This team has already deployed in a regulated public sector."

## Scope Decisions

| # | Proposal | Effort | Decision | Reasoning |
|---|----------|--------|----------|-----------|
| E1 | Tender spec pack (*pliego de prescripciones técnicas*): CPV codes, pilot lot, payment per verified recovered slot against the ledger, privacy/ENS requirements, acceptance criteria | M | ACCEPTED | Shows the procurement route; draws on the project owner's procurement-data work (Licita) |
| E2 | Standalone ledger verifier: a page plus `slotback verify ledger.jsonl` | S | ACCEPTED | Anyone can check without trusting us; reuses the day-2 verifier |
| E3 | FHIR R4 interface (`Appointment`/`Slot`/`Patient`) beside the simple REST API | M | ACCEPTED | Answers IT's integration question; medium schedule risk on day 2 |
| E4 | Full DPIA draft (Art. 35, AEPD structure, 12–15-risk register, data flow, residual risk) | M | ACCEPTED | The data protection officer is the stakeholder who can veto the deal |
| E5 | Bilingual exec pack: readout and memo in Spanish first, English too | S | ACCEPTED | The real buyer reads Spanish; shows readiness for Spain |
| E6 | Live cost meter (cost per recovered slot) plus a "tamper" demo on the replay | S | ACCEPTED | Two memorable moments for the video and the live demo |

## Accepted Scope (added to this plan)

- **E1, tender spec:** `docs/04b_tender_spec.md`, Spanish with an English summary, written on day 4. Watermarked "Illustrative – fictional buyer – not legal advice". It cites LCSP 9/2017 and the relevant procurement routes. From Licita it pulls **only CPV codes and generic buying routes**; no buyer or award names, and the final hard-rules grep covers this file.
- **E2, standalone verifier:** `slotback verify <bundle>`, where the bundle is a zip of `ledger.jsonl` + `list_snapshots.jsonl` + `head.json`. There is also a `/verify` page (dashboard surface #8), built on day 5, reusing `ledger.verify()`. What each input checks:

  | Input | Checks |
  |---|---|
  | Full bundle | hash chain, signed head, list order, identity before detail |
  | Ledger only | hash chain and identity before detail; the report says "list order: not checked (no snapshots)" |

  Upload limits: 5 MB cap, schema-validated, never executed or shown as raw HTML, rate-limited (10/min per IP), and behind the same access code as Try-it.
- **E3, FHIR R4 interface:** **documented by default** (approved change, D5). `05_solution_design.md` maps `Appointment`/`Slot`/`Patient` to our models. The code (FHIR-shaped endpoints over the internal service layer) is a **day-5 stretch** goal. If built: read endpoints are public, write endpoints sit behind the access code, and it is labelled "FHIR-shaped subset, not a certified server".
- **E4, DPIA draft:** `docs/05b_dpia_draft.md`. Skeleton and risk register on day 3, alongside the conversation design; finished on day 6. Watermarked "DRAFT – fictional hospital – not legal advice".
- **E5, bilingual exec pack:** `readout/es/` is written **on day 6**: the about-10-slide deck plus the 1-page memo. `readout/en/` on day 7 is a translation. If day 7 runs short, the English deck becomes a 2-page summary.
- **E6, cost meter and tamper button:**
  - **Cost meter:** a console tile for cost per recovered slot = (ElevenLabs agent minutes × verified plan rate + telephony minutes × the verified Twilio rate) ÷ recovered slots. Rates and their date come from the day-3 pricing check. Badged SIMULATED wherever the minutes are simulated.
  - **Tamper button:** on the ledger replay, edits one event in an in-memory copy only, and the verifier fails at that link. Built on day 5.

**Schedule impact:** about 5–6 build hours added. Day 2 and day 7 load is unchanged; the extra work goes to days 3–6.

**Cut triggers** (replace the earlier single list):
- **Day-5 trigger** (if the core surfaces aren't done by the end of day 5): drop the FHIR code first; it stays documented.
- **Day-6 trigger** (if surfaces are still unfinished): cut in this order: landing page → Try-it → eval report page → ROI calculator.
- **Never cut:** the console, call detail, impact plus ledger replay, E2 verifier, E6 meter and tamper button.

**Updates to the approved design:**
- **Success criteria** gain the following:
  - 04b, 05b, `readout/es/` and `readout/en/` exist;
  - `/verify` passes the day's bundle and fails a tampered bundle and a wrong signed head;
  - the hard-rules grep covers every new file.
- **Doc ↔ phase table** gains:

  | Doc | Phase |
  |---|---|
  | 04b_tender_spec | 4 |
  | 05b_dpia_draft | 5 |
  | readout/es, readout/en | 9 |

## Deferred to TODOS.md
- None from this review.


## Late scope additions ("build it now", 2026-10-16)

| # | Item | Effort | Notes |
|---|---|---|---|
| E7 | **Postgres** replaces SQLite. Use a free managed Postgres in an EU region (e.g. Neon or Supabase free tier; check on day 1). Slot claim uses `SELECT … FOR UPDATE` plus a version column. SQLite is not used anywhere (tests run on Postgres, eng 1A). | M | Also solves OV6: the evidence survives Space restarts. Reseed becomes an explicit `make seed`, not done on every boot. Connection string is an HF/GitHub secret. Adds a dependency on an external DB, so `deploy_check` tests the connection |
| E8 | **Inbound agent**: patients call in (browser widget / Twilio number) to cancel or reschedule. A cancellation immediately triggers backfill. Same identity flow (D13), call-token binding (D15), ledger and service layer. A second agent config `agent/inbound/`. | L | Shown as phase 2 of the scale path. Note: ElevenLabs' own inbound scheduling tutorial exists [S4], so the differentiator is "inbound cancel → instant ordered backfill", not inbound booking |

**Schedule impact:** about 4–6 more build hours. E7 lands on day 1 (with the scaffold). E8 goes on day 5. The day-6 cut trigger now starts: landing page → **E8 inbound** → Try-it → eval report page → ROI calculator. E7 is never cut once in place.


## Engineering Review Decisions (2026-10-16)

All approved.

| # | Area | Decision |
|---|---|---|
| ENG-0 | Scope | Complexity check triggered; proceeded with full scope |
| 1A | Arch | **All tests run on Postgres** (local Docker `postgres:16` + GitHub Actions service container, fresh schema per test). SQLite removed entirely |
| 1B | Arch/Perf | At most 2 DB round trips per tool (claim + ledger write as one SQL statement), pooled warm connections, wake script pings the DB, deploy_check measures p95 from the Space. If over budget: Space in an EU region or a paid Space |
| 1C | Security | Inbound calls start with an **unbound token**; only `verify_identity` works until it binds the token to that one patient; lockout keyed on phone number + patient |
| 2A | DRY | Safety rules written once as `agent/fragments/*`; `push.py` builds the 4 configs (outbound/inbound × demo/production-reference); a snapshot test checks every config has every safety fragment |
| 2B | DRY | Pydantic models are the single source for tools; ElevenLabs tool schemas are generated; CI fails if the committed schemas are stale |
| 2C | DRY | `metrics/registry.json` holds each number with its provenance; the dashboard reads it; docs and readout use `{{metric:...}}` placeholders filled by a script; CI fails on stale or unfilled ones |
| 3A | Tests | Playwright smoke suite for all 8 pages (states, provenance tags, gated actions), in `core` CI and in deploy_check |
| 3B | Tests | Generator determinism (seed → output hash) and calibration (12% ±0.5 pt; age and booking-delay associations; strictly ordered waiting lists) |
| 4A | Perf | One in-process board cache shared by all viewers (3 s); polling pauses on hidden tabs; the DB can sleep when nobody is watching |
| 4B | Perf/Arch | Hash chain is **per hospital per day**; writes lock that day's head row; the signed daily head is that chain's last hash |

Layer-1 built-ins to use (confirm in the day-3 spike): ElevenLabs conversation-initiation webhook for per-call dynamic variables (D15); ElevenLabs custom headers/secrets on webhook tools (D11); `cryptography` Ed25519; Hypothesis; Postgres `SELECT … FOR UPDATE`; `slowapi` rate limits; `uv build` for `slotledger`.

## NOT in scope
- Calling any number other than the developer's own phone (an allow-list enforces this), including by visitors.
- A certified FHIR server or a real integration with any hospital information system.
- Predicting no-shows to free slots (Annex III exposure; see the approved design).

## Strategy and Scope Review Decisions (2026-10-16)

Sections 1–11, all approved.

| # | Area | Decision |
|---|---|---|
| D5 | Scope | E3 FHIR: documented by default, code on day 5 as a stretch |
| D6/D8 | Accounts | Has ElevenLabs + Hugging Face. **Twilio added for one recorded demo call to the developer's own phone** (number allow-listed, the developer plays a synthetic patient, cost quoted first). Browser widget session is the fallback |
| D7 | Repo | Private GitHub repo `digvijaysingh-ai/slotback` on day 1 for CI (confirm before the first push); public later, separately |
| D9 | Evals | Quality/tone scored by ElevenLabs' built-in evaluation (no separate LLM-judge key); advisory only |
| D10 | Arch | Slot claim and ledger event in ONE transaction via `record_and_apply()`; property test: ledger ⇔ slots always agree |
| D11 | Security | Tool webhooks need a secret header (HF secret + agent config) plus a per-IP rate limit; rejections logged |
| D12 | Evals | Simulation errors (429/5xx/quota/empty transcript): retry 2× with backoff, then ERRORED; any ERRORED in the smoke set fails the gate |
| D13 | Security | Max 2 failed identity checks per call, then callback message; 3 failed calls in 24h locks automated calls for that patient and flags staff; every attempt logged in the ledger |
| D14 | Errors | Missing signing key: refuse to sign, UNSIGNED banner. Seed failure fails the health check. Rescues log call_id/pid/tool/slot_id. 422 errors the agent can read; agent never invents slots |
| D15 | Security | Tools are bound to a per-call token issued when the call starts (passed as an ElevenLabs dynamic variable); any `pid` the LLM sends is ignored; a foreign pid returns 403 |
| D16 | Privacy | Two agent profiles: `demo` (recording on, own phone only, AI and recording notice) and `production-reference` (zero retention, no recording) |
| D17 | Security | Dashboard is read-only in public; every action (kill switch, campaign, callback) needs the access code and is logged |
| D18 | Data flow | Campaign: one call per appointment per campaign day (unique key), calling window Mon–Sat 9–20 Europe/Madrid, max 2 attempts |
| D19 | Data flow | Reschedule is an atomic swap in one transaction; a plain cancel only after read-back and an explicit yes |
| D20 | Code | Backfill state machine as a transition table; any other move raises IllegalTransition; the docs diagram is generated from the table |
| D21 | Tests | Leak-detector known-answer set (~25 transcripts with planted leaks, plus controls): 100% caught, ≤2 false alarms, in CI |
| D22 | Tests | Fake clock injected everywhere; CI `core` job (deterministic) on every push; `evals-smoke` only when agent/ or evals/ change, or run manually |
| D23 | Perf | Tool budget p95 ≤ 300 ms server time; agent filler phrase on slow tools; p50/p95 per tool on the console; wake the Space before demos |
| D24 | Observability | ElevenLabs `conversation_id` is the trace ID on logs, ledger and calls; JSON logs carry only pid/call_id/tool/outcome/latency (enforced by a test); 4 console alerts |
| D25 | Deploy | "Demo vs production" table (region, residency, retention, telephony) in the README, 05, the DPIA and the readout |
| D26 | Deploy | `scripts/deploy_check.py` gates the agent push: health, seed counts, signed tool call, verifier, unsigned call rejected, p95 |
| D27 | Expansion | ACCEPTED: `slotledger/` as a standalone package (record_and_apply, verify, sign_head, CLI), no Slotback imports, own README; built from day 2 |
| D28 | UX | Provenance tag on every number: SIMULATED / BENCHMARK [source, year] / SYNTHETIC / MEASURED, with a hover showing the source; shared by the dashboard and the readout |

## Independent Review Findings (2026-10-16)

OV = independent reviewer finding on the strategy and scope plan.

| # | Finding | Decision |
|---|---|---|
| OV1 | The plan leans on engineering, but a decision-maker judges the strategy in about 5 minutes | **B: keep the current plan** (breadth plus engineering depth stays; no extra time limits) |
| OV2 | A ledger signed by the vendor is circular as a bill | **A:** bill only fills that match the hospital's own booking record (reconciled daily). The ledger is tamper-evident evidence; the hospital's booking system is the source of truth. The "auditor verifies without trusting us" claim is downgraded in 05, 04b, the README and the readout |
| OV3 | "Recovered slot" isn't defined | **A:** billable = filled by the agent AND attended, minus the baseline refill rate from the SMS-only arm. Adds an `attended` ledger event (synthetic in the demo). Used in 04, 04b and the pilot go/no-go |
| OV4 | Speech recognition for identity is tested last | **A:** on day 3, 5–10 browser-widget voice tests of the identity step; if it's unreliable, change the factors (e.g. DOB + last 3 digits, spelled-out digits) |
| OV5 | Simulations may not reach the webhooks before deploy | **A:** on day 3, check that the Simulation API calls real webhooks and dynamic variables; otherwise the day-4 gate is labelled "mock-tool evals" until the deploy |
| OV6 | Reseeding wipes the evidence | **A:** bundles (ledger + snapshots + signed head) are stored in Postgres; the showcase day's bundle is also committed under `evidence/` (HF dataset dropped, eng EOV7); /verify and the replay read stored bundles |
| OV7 | A Twilio trial ruins the recording | **B: the browser widget is the main recorded demo; a Twilio phone call is a bonus** if a trial or upgrade works cleanly. Success criterion → "one recorded voice session (widget; phone if available)" |
| OV8 | Text simulations can't measure audio behaviour | **B: keep the current plan** (all metrics reported from simulations). The D28 provenance tags still mark them SIMULATED; latency from text simulations is labelled "text-sim turn latency", not voice latency, to stay within the "no invented results" rule |

## NOT in scope
- Calling any number other than the developer's own phone (allow-listed).
- A certified FHIR server, or any real integration with a hospital information system.
- Freeing slots on a predicted no-show (Annex III).
- Spanish phone number / regulatory registration for Twilio.

## What already exists
- `docs/01–03` (committed d85e7cb): sizing, stakeholders, discovery, use-case scoring. Reused as-is; 01 §2.5 gets the synthetic profile.
- `research/sources.md`: verified sources [S1]–[S6]. Reused for every BENCHMARK provenance tag (D28).
- ElevenLabs platform: agents, workflows, tools/webhooks, batch calling, voicemail detection, Tests, Simulation API, built-in evaluation. Used directly, not rebuilt.
- No application code yet (greenfield).

## Dream state delta
```
CURRENT (today)                 THIS PLAN (2026-10-23)                     12-MONTH IDEAL
docs 01–03, no code      --->   working agent + ledger + gate + 8 UI   --->  a deployment kit a health service
                                surfaces + tender + DPIA + ES readout,       procures: live pilot, reconciled billing
                                synthetic, demo-hosted (non-EU)              against the hospital's system, EU-resident,
                                                                             slotledger offered as a platform feature
```
What remains after this plan: a real pilot (fictional for now), EU-resident hosting, reconciliation against a real hospital information system, and an inbound agent.

## Failure Modes Registry
```
CODEPATH               | FAILURE MODE                  | RESCUED? | TEST?            | USER SEES?                    | LOGGED?
-----------------------|-------------------------------|----------|------------------|-------------------------------|--------
verify_identity        | ASR mishears DOB/ID           | Y        | Y (OV4 + persona)| re-ask; then callback msg     | Y
verify_identity        | brute-force across calls      | Y (D13)  | Y (persona)      | lockout, staff flag           | Y
any tool               | jailbreak → foreign pid       | Y (D15)  | Y (persona)      | "I can only discuss..."       | Y
accept_backfill        | CAS lost / hold expired       | Y        | Y (property)     | "slot just taken"/staff call  | Y
record_and_apply       | crash mid-write               | Y (D10)  | Y (crash inject) | consistent state, no partial  | Y
reschedule             | hang-up mid-swap              | Y (D19)  | Y (persona)      | keeps exactly one appt        | Y
campaign runner        | rerun / restart               | Y (D18)  | Y (property)     | nobody called twice           | Y
tool webhook           | Space asleep / >10s           | Y        | Y (deploy_check) | apology + callback            | Y
tool webhook           | no/invalid secret             | Y (D11)  | Y (deploy_check) | 401, nothing changes          | Y
sim runner             | 429/5xx/quota/empty           | Y (D12)  | Y (unit)         | ERRORED, gate fails           | Y
leak detector          | misses a leak                 | Y (D21)  | Y (known-answer) | gate fails on known-answer set| Y
sign_head              | key missing                   | Y (D14)  | Y (unit)         | UNSIGNED banner               | Y
boot reseed            | seed fails                    | Y (D14)  | Y (deploy_check) | health check fails loudly     | Y
evidence               | restart wipes ledgers         | Y (OV6)  | Y (deploy_check) | bundles persist in dataset    | Y
billing                | fill not attended / no match  | Y (OV2/3)| Y (unit)         | not billable, shown in recon  | Y
```
CRITICAL GAPS: 0.

## Implementation Tasks
- [x] **T1 (P1)** slotledger: `record_and_apply`, hash chain, `verify`, `sign_head`, bundle export. Source: D10, D27, OV6. Files: `slotledger/`. Verify: `pytest slotledger -q` + tamper test.
- [x] **T2 (P1)** domain: transition-table state machine, atomic swap, holds, fake clock. Source: D19, D20, D22. Files: `slotback/domain/`. Verify: Hypothesis suite.
- [x] **T3 (P1)** tools API: call-token binding, secret header, rate limit, 422 errors, minimal JSON logs with trace ID. Source: D11, D14, D15, D24. Files: `slotback/api/tools.py`. Verify: integration tests + log-content test.
- [x] **T4 (P1)** identity: 2 tries per call, 24h lockout, ledger events. Source: D13. Verify: unit + social-engineering persona.
- [x] **T5 (P1)** campaign runner: unique key, calling window, attempt cap, Twilio allow-list. Source: D18, D8. Verify: property test "run twice → one call".
- [x] **T6 (P1)** evals: ERRORED handling, leak known-answer set, two CI jobs, ElevenLabs built-in scoring. Source: D9, D12, D21, D22. Files: `evals/`, `.github/workflows/`. Verify: CI green; known-answer set 100% caught.
- [x] **T7 (P1)** day-3 platform spike: simulations → real webhooks + dynamic variables; pricing; residency; widget identity voice test. Source: OV4, OV5, D25. Output: `docs/DECISIONS.md` entries.
- [x] **T8 (P1)** `scripts/deploy_check.py` + wake script. Source: D26, D23. Verify: run against Space.
- [x] **T9 (P1)** billing definition + reconciliation (`attended` event, matched-to-booking, SMS baseline). Source: OV2, OV3. Files: `slotledger/`, `docs/04*`. Verify: unit test on reconciliation.
- [x] **T10 (P2)** provenance tag component + demo-vs-prod table. Source: D25, D28. Files: dashboard, README, 05, readout.
- [x] **T11 (P2)** agent profiles `demo` / `production-reference`; tool latency budget + filler phrase. Source: D16, D23. Files: `agent/profiles/`.
- [x] **T12 (P2)** dashboard actions behind access code with logging. Source: D17.

## Independent Engineering Review Findings (2026-10-16)

EOV = independent engineering reviewer finding, with the decision taken.

| # | Decision |
|---|---|
| EOV1 | **Signed post-call webhook** (`/hooks/post-call`, signature checked) feeds no-answer, voicemail and completed outcomes into the state machine. A **timer sweep** expires holds and moves to the next patient. It runs on every request and from a GitHub Actions cron every 5 min. Built on day 2 |
| EOV2 | **Platform spike (T7) moves to the morning of day 1.** It also sets the ElevenLabs credit cap. If the widget can't carry a trusted token, widget sessions start unbound and bind on `verify_identity` (the 1C pattern). Outbound phone calls use the server-issued token |
| EOV3 | A **private HF Space from day 1–2** is the webhook target for CI and simulations. Day 6 only makes it public, after confirmation |
| EOV4 | The **demo database sits in the Space's region**. EU residency is listed as "production" in the D25 table. The wake script wakes the database too |
| EOV5 | **Each eval run gets its own hospital ID** (its own chain and slots, its own fixture). The showcase day is read-only |
| EOV6 | **Property tests run on the pure in-memory domain**. Postgres runs a focused integration set: compare-and-swap claim, `FOR UPDATE`, crash between steps, atomic swap, the full synthetic day. No SQLite anywhere (refines 1A) |
| EOV7 | **This file is the single source of truth.** The approved design doc is superseded wherever it conflicts. The HF dataset is dropped; bundles live in Postgres plus `evidence/` |
| EOV8 | The independent review suggested trimming the infrastructure. **Kept the current plan** (4 configs, metrics registry, Playwright on 8 pages, inbound code). The day-6 cut trigger still drops the E8 code first if time runs short |

## Revised 7-day schedule (reconciled)

| Day | Build |
|---|---|
| 1 (Fri 17) | **Morning:** platform spike T7 (tool auth headers; widget and outbound token options; do simulations call real webhooks with dynamic variables; built-in evaluation; credit cap; pricing; regions). Free Postgres co-located with the Space. `uv` scaffold, ruff, pytest, Docker Postgres for tests. Seeded generator with determinism and calibration tests. Private repo plus CI `core` job (needs confirmation before the first push). Docs: DECISIONS, OPEN_QUESTIONS, 00 draft, 01 §2.5 |
| 2 (Sat 18) | `slotledger` (per-hospital-per-day chain, `record_and_apply`, verify, signed head, bundle). Pure domain with the transition table, atomic swap, holds, fake clock; Hypothesis on the pure domain. Postgres integration set. Tools API (secret header, token binding, 422 errors, minimal logs). **Post-call webhook and timer sweep.** **Private Space deployed** with deploy_check. Docs: 05 |
| 3 (Sun 19) | Agent fragments, `push.py` (4 configs, generated tool schemas). Widget identity voice tests (OV4). Wireframes for the 8 pages. DPIA skeleton. Docs: 06 |
| 4 (Mon 20) | Evals: one hospital ID per run, leak known-answer set, ERRORED handling, `evals-smoke` CI against the private Space, built-in scoring. Billing reconciliation. Docs: 08, 04, 04b. **Day-4 check: deterministic gate green on real simulation output** |
| 5 (Tue 21) | Dashboard, 8 pages to the minimum bar, with the metrics registry, provenance tags, board cache, gated actions; Playwright smoke. E2 verifier, E6 cost meter and tamper button. E8 inbound agent. E3 FHIR code (stretch). Docs: 07. **Day-5 cut trigger** |
| 6 (Wed 22) | Make the Space public (after confirmation). Recorded widget session (main); Twilio phone call (bonus, cost quoted first). Judge calibration. Readout `es/`. DPIA finished. Docs: 09, 10. **Day-6 cut trigger** |
| 7 (Thu 23) | Readout `en/`, Product memo, README case study, hard-rules grep over all files |

## Worktree parallelization

| Step | Modules | Depends on |
|---|---|---|
| Spike + scaffold + DB | repo root, `infra/` | — |
| Generator | `slotback/data/` | scaffold |
| slotledger | `slotledger/` | scaffold |
| Domain | `slotback/domain/` | scaffold |
| Tools API + hooks + sweep | `slotback/api/`, `slotback/services/` | domain, slotledger |
| Agent configs | `agent/` | tools API (schemas) |
| Evals | `evals/`, `.github/` | agent, private Space |
| Dashboard + E2/E6 | `slotback/dashboard/`, `metrics/` | services |
| Docs (04/04b/05/05b/06–10, readout) | `docs/`, `readout/` | decisions only |

- **Lane A:** scaffold → API → evals (sequential, the critical path).
- **Lane B:** `slotledger/` (after scaffold, in parallel with C).
- **Lane C:** `slotback/domain/` + `slotback/data/`.
- **Lane D:** `docs/` + `readout/` (independent throughout).
- **Lane E:** dashboard (after API).

**Order:** scaffold first; then B + C + D in parallel worktrees; merge; then A (API) → agent → evals, with E in parallel.

**Conflict flags:**
- B and C both touch `pyproject.toml`; coordinate dependency additions.
- E and A both touch `slotback/services/` read models; E should only read.

## Engineering Implementation Tasks (adds to T1–T12)
- [x] **T13 (P1)** — api — Signed post-call webhook + timer sweep (per request + Actions cron). Surfaced by: EOV1. Files: `slotback/api/hooks.py`, `.github/workflows/sweep.yml`. Verify: unanswered call → next rank offered; expired hold swept with a fake clock.
- [x] **T14 (P1)** — infra — Move the platform spike to day 1; set the credit cap; widget binds on verify if needed. Surfaced by: EOV2. Verify: `docs/DECISIONS.md` entries for each platform fact.
- [x] **T15 (P1)** — infra — Private HF Space on day 1–2 + deploy_check. Surfaced by: EOV3. Verify: `evals-smoke` reaches the Space from CI.
- [x] **T16 (P1)** — evals — One hospital ID and fixture per eval run; showcase day read-only. Surfaced by: EOV5. Verify: after a nightly run the showcase head hash is unchanged.
- [x] **T17 (P1)** — tests — Pure-domain property tests + Postgres integration set (Docker locally, service container in CI). Surfaced by: 1A, EOV6. Verify: `core` CI under 5 min.
- [x] **T18 (P1)** — api — Inbound/widget unbound token, bind on verify. Surfaced by: 1C, EOV2. Verify: every tool refused before verification; foreign patient blocked after.
- [x] **T19 (P2)** — agent — Fragments + 4 composed configs + generated tool schemas + drift checks. Surfaced by: 2A, 2B. Verify: snapshot test; CI fails on a stale schema.
- [x] **T20 (P2)** — metrics — Registry + placeholder filler + CI check. Surfaced by: 2C. Verify: no unfilled `{{metric:}}` in docs or readout.
- [x] **T21 (P2)** — tests — Playwright smoke on 8 pages. Surfaced by: 3A. Verify: green in `core` and in deploy_check.
- [x] **T22 (P2)** — data — Generator determinism + calibration tests. Surfaced by: 3B.
- [x] **T23 (P2)** — perf — ≤2 round trips per tool, pooling, co-located DB, warm-up; board cache; per-day chain lock. Surfaced by: 1B, 4A, 4B, EOV4. Verify: deploy_check p95 ≤ 300 ms.
- [x] **T24 (P2)** — docs — Reconcile: design doc marked superseded where it conflicts; this file is the source of truth. Surfaced by: EOV7. **Done in this review.**

## Failure modes added by the engineering review
```
CODEPATH            | FAILURE                         | TEST? | HANDLED?          | USER SEES
post-call webhook   | bad signature / replayed event  | Y     | reject 401, dedup | nothing changes
timer sweep         | Space asleep, cron missed       | Y     | next request runs | hold expires late (≤5 min)
token binding       | widget token forged             | Y     | bind on verify    | tools refused until verified
eval isolation      | eval writes into showcase day   | Y     | per-run hospital  | showcase untouched
DB co-location      | Neon cold start                 | Y     | wake script       | first call after warm-up OK
```
CRITICAL GAPS: 0.

## Design Review Decisions (2026-10-16)

**Visual direction:** B "Control room": dark, dense, calm, one blue accent, amber SIMULATED badge. Reference: approved mock-up variant B of the Impact replay page.
**Type (4A):** IBM Plex Sans (UI) + IBM Plex Mono (ledger, hashes, codes, tags), with tabular figures for every number. Inter is dropped.
**Design system (5A):** `DESIGN.md` is produced in a design-system pass right after this review, seeded from direction B. It must include a **light token set** for the printed/projected readout slides.
**Language (7A):** the public demo opens in **English**, with a prominent ES toggle remembered per visitor. Agent calls, transcripts and `readout/es/` stay Spanish; transcripts show an English gloss line.

### Information architecture (Pass 1)
Navigation (left rail, current page marked): Impact · Console · Calls · ROI · Evals · Verify · Try. The **landing page is kept (decision 1B)** as one composition, not a grid of boxes: the recovered-slots result vs SMS-only (SIMULATED), one sentence on what Slotback is, one primary button "See the live day →" to Impact, and a secondary link to the case study. A context bar on every page reads: "Fictional hospital · synthetic data · simulated results are labelled".

| Page | 1st | 2nd | 3rd |
|---|---|---|---|
| Landing | Recovered slots vs SMS-only (SIMULATED) | One-line what & why | "See the live day →" |
| Impact | Recovered-slots number vs SMS-only | Day timeline / replay | Ledger feed + verified status, tamper |
| Console | Live call board by status | Exceptions queue for humans (one-click callback) | Freed-slot feed, cost meter, alerts, kill switch |
| Call detail | Outcome + flags (privacy, escalation) | Transcript ⇄ tool-call timeline | Ledger events, audio (demo calls only) |
| Evals | Gate status PASS / FAIL / ERRORED | Scenario × persona matrix | Leak known-answer result, version comparison |
| ROI | Break-even + € per recovered slot | Sliders, each with a provenance tag | Sensitivity |
| Verify | Drop zone (bundle) | Pass/fail per check | What each check proves (plain language) |
| Try | Access code / start | Persona + scenario picker | Live tool-call feed beside the session |

### Interaction states (Pass 2)
| Feature | Loading | Empty | Error | Success | Partial |
|---|---|---|---|---|---|
| Any page after the Space wakes | "Waking the demo (up to 30 s)" with a progress bar; never a blank page | — | "The demo server didn't start. Retry · Watch the recorded demo" | Page renders | — |
| Impact | Skeleton timeline | "No slots were freed today. Freed slots appear here as patients cancel." + "Replay a past day" | "Couldn't load the ledger" + retry | End state with verified chain | Chain UNSIGNED: amber banner "Head not signed — verification limited" |
| Console board | Skeleton rows | "No calls scheduled today. Next campaign: Mon 09:00." + "Start a demo campaign" (access code) | Row-level error with retry; webhook-error alert | Live rows | "Calling paused (kill switch)" banner showing who paused it and when |
| Exceptions queue | — | "Nothing needs a human right now." | — | Items with summary + callback | — |
| Call detail | Skeleton | "This call has no transcript (voicemail / no answer)." | "Call not found" + back | Full view | "Transcript still processing" note |
| Evals | Skeleton matrix | "No eval run yet. Run the smoke suite." | Run failed with log link | PASS banner | "3 of 12 scenarios ERRORED — gate not green" amber banner |
| ROI | — | Prefilled with defaults (never empty) | Invalid input inline next to the slider | Live recalculation | — |
| Verify | Progress "Checking 3,112 events…" | Drop zone with "Try the sample bundle" | Specific: "Not a Slotback bundle" / "File over 5 MB" | Green checks per invariant | Ledger-only upload: "List order: not checked (no snapshots)" |
| Try | Connecting… | Access code prompt | "Monthly demo minutes used up. Watch the recording." | Live session | Session cap warning at 2:30 |

### User journey (Pass 3): a first-time visitor's 5 minutes
| Step | Visitor does | Feels | Supported by |
|---|---|---|---|
| 1 | Opens the URL (landing) | "What is this?", then oriented in 5 s | One composition: result + one sentence + one button |
| 2 | Clicks "See the live day" | "It already worked": answer visible | Impact opens on the **end state** (3A) |
| 3 | Presses "Replay the day ▶" | Watching it happen | 60 s replay: markers step through freed → offering r1/r2 → filled; counter climbs; ledger lines appear in sync. Pausable and scrubbable; reduced-motion shows steps without animation |
| 4 | Presses "Tamper" | "Oh, it's provable" | One event changed in a memory copy; the verifier turns red at the exact `#seq`; a "Restore" button |
| 5 | Downloads the bundle → Verify | Trust without trusting us (tamper-evident) | Verify page passes the bundle and explains each check |
| 6 | Opens a call | "It's careful with patients" | Disclosure → identity → read-back visible in the transcript and tool timeline |
| 7 | Evals / ROI | "This team thinks like a deployer" | Gate status first; ROI break-even first |

### Responsive & accessibility (Pass 6)
- **Desktop ≥1024 px:** full three-region layout (nav, workspace, context panel).
- **Tablet 768–1023 px:** the ledger/context panel moves below the main workspace; nav collapses to icons with labels on hover/focus.
- **Phone <768 px:** a deliberate **read-only summary**: headline number, replay as a vertical event list, verify status, "Watch the 3-minute video". No actions on phones.
- **Accessibility:**
  - WCAG AA (body text ≥4.5:1, checked on both dark and light token sets); body text ≥16 px.
  - Status is always icon + text, never colour alone.
  - Full keyboard control (replay play/pause/scrub, tamper, restore, verify upload, nav), with a visible focus ring.
  - ARIA landmarks (`nav`, `main`, `complementary`).
  - The counter is announced to screen readers politely, at most every 5 s.
  - `prefers-reduced-motion` is respected; 44 px touch targets.

### Unresolved design decisions
- None. The visual system is in `DESIGN.md` (written 2026-10-16).
