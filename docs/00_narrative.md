# 00 · Narrative

**What this is:** the story behind Slotback, at three lengths, for a hospital director and for anyone evaluating the deployment.
**Rules it follows:** the customer is fictional (*Hospital General (fictional)*, part of a regional public health service in Spain). Public figures are benchmarks from other regions, each with source and year. Every number about Slotback's own performance is a placeholder filled from `metrics/registry.json` and labelled SIMULATED, because there has been no real pilot.

---

## The one sentence

> **Slotback turns the appointments patients can't keep into appointments someone on the waiting list gets, and it proves each one.**

Shorter form for a slide: *recovered slots, not reminders.*

---

## 30-second pitch

Spanish public hospitals lose roughly one specialist appointment in ten to no-shows. In one health area that was 13.8% of 400,761 appointments, costing about €3.4M a year (BENCHMARK [S2, 2013–14]). The top reasons patients give are that they forgot or never got the message (46% combined, [S2]). SMS reminders already handle forgetting cheaply. What they can't do is take a cancellation and hand the slot to the next patient on the list before the day.

Slotback is an ElevenLabs voice agent that calls patients a few days ahead to confirm, cancel or reschedule. When a slot frees up, it calls the waiting list strictly in the hospital's own order and books whoever says yes. Every recovered slot is written to a tamper-evident ledger and reconciled against the hospital's booking system, so the hospital can pay per verified recovered slot instead of per minute.

---

## 2-minute pitch

**The problem.** No-shows in Spanish specialist outpatient clinics run from about 6% to 14% depending on region and year (BENCHMARK [S5, 2024]; [S6, 2011]; [S2, 2013–14]). In the best-documented case the cost was about €61 per missed appointment (BENCHMARK [S2, 2013–14], our calculation). Waiting lists are political: in one region, delay in specialist care was the top cause of written complaints (25.1% of 14,254 in 2013, BENCHMARK [S1]).

**What's been tried.** Reminder calls work, and one regional health service announced exactly that plan in 2015: phone patients to "confirm appointments and reassign freed slots" [S1]. The constraint is staff time. Admissions teams can't make enough calls, and the phone lines patients would use to cancel are saturated [S3].

**Why voice and not SMS.** Our own reference study concludes SMS is the most cost-effective fix for forgetting [S2], and we agree. So we don't sell a better reminder. We sell the loop SMS can't run:
1. a two-way call that turns a silent no-show into an early cancellation;
2. an immediate offer of that slot to the next patient on the list, in the hospital's order;
3. reach to patients whose SMS never lands (out-of-date numbers, [S5]) or who don't act on a text link.

**What we built.** A working prototype on a synthetic clinic day: outbound agent, tool webhooks into a mock scheduling API, a backfill state machine with 10-minute holds, and the **Backfill Ledger**, a hash-chained record of every offer and booking with a signed daily head. A panel can replay the day, tamper with one event and watch the verifier name it.

**How it's bought.** A pilot small enough for a minor contract (*contrato menor*, services under €15,000 excl. VAT, LCSP 9/2017), one high no-show specialty, 90 days, SMS-only as the control arm. Billing per recovered slot counts only fills that the agent made, that the patient attended and that match the hospital's own booking record, minus the refill rate the SMS-only arm achieved anyway.

**Why it's safe to say yes.** The agent discloses it's an AI, verifies identity before saying anything (even the specialty is health data), leaves only a callback number on voicemail, hands off to a human on request, never gives clinical advice and never decides priority. That last point keeps it outside the AI Act's Annex III high-risk category for access to public healthcare.

**Results so far:** simulated only. On the synthetic showcase day the agent recovered <!--m:recovered_slots-->14<!--/m--> slots (SIMULATED), with <!--m:privacy_leaks-->0<!--/m--> privacy leaks across <!--m:eval_scenarios_total-->15<!--/m--> simulated test conversations (SIMULATED). The pilot exists to replace these with measured numbers.

---

## 10-minute pitch (talk track)

Timings are a guide. Each block names the artefact to show.

| Min | Block | Say | Show |
|---|---|---|---|
| 0–1 | **The hook** | "A specialist slot that goes empty is a consultation nobody gets. Spain loses hundreds of thousands a year." Use the Valencia figure: 733,580 missed of 7.56M (9.7%, BENCHMARK [S1, 2014]). | Landing page headline |
| 1–2 | **Why it happens** | 46% forgot or never got the message [S2]. No-shows skew younger and had waited longer (mean booking delay 25.2 vs 19.2 days, [S2]). Associations, not predictions. | `01_account_brief.md` §2.1 |
| 2–3 | **The SMS objection, answered first** | SMS wins on forgetting. Voice wins on what needs a conversation: cancel now, rebook now, offer the slot now. The pilot tests voice *plus* SMS against SMS alone. | `03_use_cases.md` recommendation |
| 3–5 | **The live day** | Replay the synthetic day: a cancellation frees a cardiology slot, the agent calls rank 1 (no answer), rank 2 accepts, the slot turns green. Then press *Tamper*: the chain breaks at one `#seq`. | `/impact` replay, tamper, `/verify` |
| 5–6 | **One call, close up** | AI disclosure, identity check, read-back, care markers (◆) in the transcript, tool calls beside it. | `/calls/{id}` |
| 6–7 | **How we know it works** | Deterministic gate: ledger verifier, leak detector with a known-answer set, tool-call correctness, disclosure, read-back. Tone is advisory. All SIMULATED; text tests can't measure ASR on elderly speech. | `/evals`, `08_evals.md` |
| 7–8 | **The money** | Value per recovered slot comes from the €61 benchmark. Price per *verified* recovered slot. Show the billable definition and the break-even formula, not a promised ROI. | `/roi`, `04_business_case.md` |
| 8–9 | **How it gets bought and approved** | Pilot under a minor contract, tender spec that pays per verified slot, DPIA draft for the DPO, ENS, AI Act Art. 50. | `04b_tender_spec.md`, `05b_dpia_draft.md` |
| 9–10 | **The ask and what I'd tell Product** | 90-day pilot in one specialty with SMS-only control, go/no-go criteria, kill switch. Field notes for ElevenLabs: ASR for elderly Spanish speakers, voicemail outcomes, HIS connectors, outcome ledger as a platform feature. | `09_pilot_plan.md`, `11_product_feedback.md` |

**If interrupted early,** go straight to the replay and tamper (minutes 3–5). That is the part people remember.

---

## The champion: head of admissions

The economic buyer is the hospital director. The person who makes the pilot happen, and who would use Slotback every day, is the **head of admissions** (*jefe/a de admisión*). This persona is a composite built from the discovery guide in `02_discovery.md`, not an interview with a real person.

**Profile (hypothesis, to validate in discovery)**
- Runs a team of admissions clerks across the hospital's sites; reports to the director's office.
- Measured on waiting-list figures, complaints and how full the clinics are.
- Has seen technology projects add work: "another screen to babysit".
- Knows exactly which specialties lose the most slots and which clerks are best on the phone.

**Their week, today (hypothesis)**

| Day | What happens | Where Slotback changes it |
|---|---|---|
| Mon | Weekly waiting-list figures go to the director. Two specialties are over target. | The recovered-slots number goes into the same report, with its ledger behind it. |
| Tue | A clerk is off sick; reminder calls for Thursday's clinics don't get made. | The agent makes the routine calls; clerks get only the exceptions queue. |
| Wed | Three cancellations arrive by phone for tomorrow. Nobody has time to ring the waiting list, so the slots stay empty. | Each cancellation triggers backfill in list order within minutes, with a 10-minute hold per offer. |
| Thu | A patient complains they waited 40 minutes on the line to cancel. | The patient was called on Monday and cancelled in one minute. |
| Fri | The director asks why a clinic ran at two-thirds capacity. Answer: no-shows, no evidence. | The console shows which slots were freed, offered, filled or left unfilled, and why. |

**What wins them:** the agent does the volume; their team handles the cases that need a person; they get a number they can defend upward.
**What loses them:** a system that calls the wrong patient, says too much on a voicemail, or creates complaints they then have to answer. That's why the guardrails are in the first demo, not the last.

---

## What the project covers

The full deployment lifecycle on one problem: account research with sourced figures, discovery, use-case selection, a business case and commercial model, a solution design a data protection officer can review, a working prototype, an eval gate, a pilot plan, an executive readout in Spanish, and field notes back to the platform's product team.

The procurement material (thresholds, routes, CPV codes) draws on prior work with Spanish public procurement data; no buyer or award is named.

---

## What we never claim

- That Slotback has run in a real hospital. It hasn't.
- Any measured no-show reduction or fill rate. All Slotback numbers are SIMULATED placeholders until a pilot runs.
- That the demo is EU-resident or uses zero retention. Those are production settings (Enterprise features on the platform, see `05_solution_design.md`).
- That the ledger alone proves a bill. The hospital's booking system is the source of truth; the ledger is tamper-evident evidence that is reconciled against it.

---

## Sources

Source IDs match `01_account_brief.md`; full list in `research/sources.md`.
- **[S1]** Valencia region, Jan–Nov 2014, press report of 30 Jan 2015.
- **[S2]** Jabalera Mesa (2015), doctoral thesis, Costa del Sol health area, data 2013–14. **[S2b]** journal article, 2015.
- **[S3]** Regional ombudsman resolution, case file 1259/2021 (primary care).
- **[S5]** Galicia region, 2024 figures, press report of 28 Jan 2025.
- **[S6]** Pereira-Victorio et al. (2016), one week of Aug 2011.
