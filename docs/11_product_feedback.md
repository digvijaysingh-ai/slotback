# 11 · Field notes for ElevenLabs Product

**To:** ElevenLabs Agents Product team
**From:** Slotback deployment (independent reference deployment; fictional Spanish public hospital, synthetic data)
**Date:** 2026-10-16
**Type:** field-notes memo. Part A is what we hit while building, each item checked against the docs on 2026-10-16 and logged in `docs/DECISIONS.md`. Part B is feature requests ranked by enterprise impact; these are **hypotheses** from one prototype and the public-health context, not customer interviews.

---

## Summary

Building an outbound healthcare agent for a regulated public buyer, the platform covered the conversation well. The friction was at the edges a deployment lives or dies on: knowing a call's outcome reliably, trusting per-call context, and fitting regulated-data settings (residency, zero retention) together with outbound volume. Six observations, four requests.

---

## Part A · What we observed

| # | Observation | Impact on this deployment | Our workaround |
|---|---|---|---|
| A1 | **`simulate-conversation` is deprecated and removed on 31 Oct 2026.** Tests (`tests.create` + `agents.run_tests`) replace it; unmocked tools in Tests call the real webhook. | We had planned the eval harness on the Simulation API. A deployment that started a month earlier would now be migrating its eval suite mid-pilot. | Built the harness on Tests from day one. Each eval run gets its own synthetic hospital ID so unmocked tool calls can't touch the showcase data. |
| A2 | **Widget dynamic variables are set by the browser.** | Anything a widget session passes (patient ID, token) can be forged by the user. For a healthcare agent that means per-session context from the widget can't be trusted for authorisation. | Widget and inbound sessions start with an unbound token; only `verify_identity` works until identity is verified, which binds the token to one patient. Phone calls get a server-issued token through `conversation_initiation_client_data`, sent to our tools as a `secret__` dynamic-variable header. |
| A3 | **Voicemail does not fire `call_initiation_failure`.** | Voicemail is a core outcome for outbound reminder calls: it decides whether to retry and when to move a backfill offer to the next patient. Without an explicit event the outcome has to be inferred. | Read the outcome from the signed `post_call_transcription` webhook (transcript and termination reason) or batch-call status, plus a timer sweep that expires holds if no outcome arrives. |
| A4 | **Zero Retention Mode excludes batch calling.** | A public-health buyer will require zero retention. The outbound use case depends on batch calling. Together, production must place calls one at a time, which caps throughput and adds orchestration on our side. | Production design places calls individually from our campaign runner (one call per appointment per day, calling window, attempt cap). The demo uses neither ZRM nor batch at scale. |
| A5 | **Data residency is an Enterprise feature.** | EU residency is a near-certain requirement in a Spanish public tender and in the DPIA. A pilot-sized buyer (minor contract, under €15,000 excl. VAT under LCSP 9/2017) may not be on Enterprise. | The demo claims no residency. The tender spec and DPIA list EU residency as a production requirement; the "demo vs production" table makes the gap explicit. |
| A6 | **Billing for Tests runs is not documented.** | We couldn't predict the cost of a ~60-scenario suite or a nightly run, so we kept runs small and set a monthly spend cap. A buyer's QA team would ask the same question. | Smoke suite of 12 scenarios on agent changes only; the full suite run manually. |

What worked well and saved time: workspace secrets in tool `request_headers` (never shown to the LLM), signed post-call webhooks with an HMAC signature, and Tests hitting real webhooks, which let the deterministic gate check the actual tool calls and ledger.

---

## Part B · Feature requests, ranked by enterprise impact

Ranking = how often we expect the gap to block or slow a regulated outbound deployment × how hard it is for a deployer to work around. All four are hypotheses to test with real customers.

### 1. Explicit call outcomes for outbound, including voicemail (hypothesis: high impact)

- **Request:** a first-class outcome on every outbound call (answered by a person / voicemail / no answer / busy / failed), delivered in a signed webhook, and compatible with Zero Retention Mode.
- **Why:** every outbound use case (reminders, collections, backfill) branches on this. Inferring voicemail from transcripts is fragile and doesn't work if transcripts aren't retained.
- **Evidence from this build:** A3, A4.
- **How we'd know:** count of outbound deployments that build their own outcome inference; support tickets on voicemail handling.

### 2. Speech recognition for elderly Spanish speakers (hypothesis: high impact, hardest to work around)

- **Request:** published accuracy figures and tuning for older speakers, regional accents and number sequences (dates of birth, ID digits and letters), plus a confidence score per entity that tools can read.
- **Why:** in Spanish specialist clinics, attenders skew older (mean age 55.7 vs 51.3 for no-shows, BENCHMARK [S2, 2013–14]), and identity checks depend on numbers being heard right. A misheard date of birth means a failed check, a callback and a frustrated patient; a confidently misheard one is worse.
- **Evidence from this build:** the identity step was designed with a spelled-out-digits fallback and a two-failure limit because text tests can't measure ASR. We have not measured ASR accuracy ourselves; this is a gap in what we could test, not a finding about the model.
- **How we'd know:** identity-failure rate by age band in a pilot.

### 3. Connectors for hospital information systems (hypothesis: medium–high impact)

- **Request:** a reference connector pattern for FHIR R4 `Appointment` / `Slot` / `Patient`, and guidance for systems with no API (batch files, integration engines).
- **Why:** every healthcare deployment rebuilds the same narrow scheduling adapter. IT's first question is integration, and the answer decides the timeline.
- **Evidence from this build:** we wrote a FHIR-shaped mapping and a mock scheduling API (`05_solution_design.md`).

### 4. Outcome ledger as a platform feature (hypothesis: medium impact, strong differentiator)

- **Request:** an optional tamper-evident, per-agent outcome log: hash-chained tool results and outcomes, with a signed daily head the customer can hold and verify.
- **Why:** outcome-based pricing (pay per recovered slot, per resolved case) needs evidence both sides trust. In the vendor pages we found for appointment backfill, fill rates were quoted with no stated method or audit trail (search of 2026-10-16). A platform-level ledger would make outcome pricing easier to sell to public buyers, who must justify every payment.
- **Evidence from this build:** we built it as a standalone ledger package (now `voiceledger`, part of the voiceops kit). A vendor-signed ledger alone is circular as a bill, so billing still reconciles against the customer's own booking record; the ledger makes disputes cheap to settle.

---

## What we did not test

- Real phone calls at volume, voice latency end to end, barge-in, background noise. Our metrics come from text-based Tests and are labelled SIMULATED.
- Languages beyond Spanish and English in voice (Romanian and Arabic are stretch goals in config only).
- Enterprise settings (residency, ZRM) in practice; we only read the docs.

---

## Sources

- ElevenLabs docs and pricing pages, checked 2026-10-16; decisions and dates logged in `docs/DECISIONS.md`.
- **[S2]** Jabalera Mesa (2015), doctoral thesis, data 2013–14 (Table 29). Full list: `research/sources.md`.

## Added after the first live runs (2026-10-16, observed)

- **Tool parameters must have a description.** Creating a webhook tool fails with 422 if any body parameter has no `description` (also enums). Worth stating in the tool-config docs; our build now tests for it.
- **Tool results come back as JSON strings in Tests transcripts** (`tool_results[].result_value`). Eval harnesses that inspect results must parse them; a structured field would remove a class of harness bugs.
- **Prompt position matters for safety rules.** A rule late in the prompt ("offer a person to an upset caller") lost to an earlier one ("verify identity first") until it got its own early section. A first-class "interrupt" or priority mechanism for safety rules would make this less fragile.
- **Credits per simulated conversation** were about 580–700 for 10 turns on the free plan in our runs (from `credits_used`); publishing a per-turn figure would help customers budget eval suites.
