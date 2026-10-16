# 09 · Pilot and rollout plan

**Account:** a regional public health service in Spain · *Hospital General (fictional)*.
**Pilot:** 90 days, one high no-show specialty, **SMS + voice** against **SMS only**.
**Status:** plan. No pilot has run. Every input below is a benchmark, a synthetic profile value or a labelled assumption. Slotback outcomes appear only as `{{metric:...}}` placeholders, filled from `metrics/registry.json` and labelled SIMULATED until a real pilot replaces them.

---

## 1. What the pilot has to answer

| # | Question | Measured by | Decides |
|---|---|---|---|
| Q1 | Does adding the voice agent reduce no-shows compared with SMS alone? | No-show rate per arm | Whether the confirmation call is worth paying for |
| Q2 | How many freed slots does the agent refill that would otherwise stay empty? | Billable recovered slots (definition in §5) | The outcome price and the business case |
| Q3 | Is it safe? | Privacy incidents, wrong-patient contacts, complaints, escalations handled | Go / no-go, regardless of Q1–Q2 |
| Q4 | Do patients and staff accept it? | Opt-out rate, complaints, staff survey, handoff rate | Scale path and change plan |
| Q5 | Does the integration hold up? | Webhook error rate, tool p95, reconciliation mismatches | IT sign-off for scale |

Q3 is a gate, not a trade-off: one confirmed disclosure of health data to the wrong person pauses the pilot (§7).

## 2. Choosing the specialty

Pick one specialty with all four of:
1. a **high no-show rate** in the hospital's own baseline (from `02_discovery.md` §3);
2. a **long waiting list** that can be exported in the hospital's official order, per specialty, at least daily;
3. **short, schedulable visits** (15–20 minutes), so a freed slot is easy to offer;
4. a **head of service who agrees** and accepts that the agent never changes the list order.

Avoid for the first pilot: specialties where most visits need preparation the agent would have to explain (clinical content), and specialties with many urgent (*preferente*) referrals that staff already handle by hand.

The synthetic demo uses five specialties (cardiology, dermatology, orthopaedics, ophthalmology, gastroenterology; SYNTHETIC). The real choice comes from the baseline, not from the demo.

## 3. Design: control and treatment

| | Control arm | Treatment arm |
|---|---|---|
| Reminder | Hospital's existing SMS | Same SMS |
| Voice call | None | Agent calls 3–5 days before the appointment: confirm, cancel or reschedule |
| Freed slots | Hospital's current process (staff ring the list if they have time) | Agent offers each freed slot down the list in order, 10-minute hold per offer, until filled or out of time |
| Exceptions | Staff, as today | Staff, from the exceptions queue |

**Unit of randomisation.** Two candidates; the hospital's statistician chooses:
- **By appointment** (simplest, most power). Risk: one clerk handles both arms and changes behaviour. Acceptable for Q1.
- **By clinic day** (alternate days or a random day schedule). Cleaner for Q2, because backfill acts on the day's freed slots and both arms would otherwise compete for the same waiting list.

Recommendation: **by clinic day** for the backfill comparison, with a stratified random schedule so each weekday appears equally in both arms. Waiting-list order is never changed in either arm.

**Why SMS + voice and not voice alone.** The reference study found SMS as effective as a call against forgetting and cheaper (BENCHMARK [S2, 2013–14], citing Liew 2009 and Leong 2006). Voice has to earn its cost on top of SMS: through two-way cancellations and backfill. Testing voice alone would answer a question nobody is asking.

## 4. Sample size (two-proportion test)

For Q1 (no-show rate), per arm:

```
n = [ z(1−α/2) · √(2·p̄·(1−p̄)) + z(1−β) · √(p₁(1−p₁) + p₂(1−p₂)) ]² / (p₁ − p₂)²
p̄ = (p₁ + p₂) / 2
```

**Illustrative inputs (ASSUMPTIONS, to be replaced by the hospital's baseline):** α = 0.05 two-sided (z = 1.96), power 80% (z = 0.8416), control no-show rate p₁ = 12% (the fictional hospital's SYNTHETIC profile, inside the 5.75–14.6% benchmark range [S5, 2024]; [S6, 2011]).

| Assumed treatment no-show rate p₂ | Detectable difference | Appointments per arm |
|---|---|---|
| 10% | 2 points | ≈ 3,841 |
| 9% | 3 points | ≈ 1,638 |
| 8% | 4 points | ≈ 882 |

*Our calculation from the formula above; inputs are assumptions, not predictions.*

For Q2 (refill rate of freed slots), the same formula with freed slots as the unit. Illustrative ASSUMPTIONS: control refill 20%, treatment refill 40% → ≈ 82 freed slots per arm. The real control rate is the "late cancellations refilled" figure requested in discovery.

**Feasibility check (SYNTHETIC):** if the pilot specialty handles about 40,000 appointments a year (an assumption for a specialty at a 380,000-appointment hospital), 90 days gives roughly 10,000 appointments, about 5,000 per arm. That covers a 3-point difference. If the real specialty is smaller, either extend to 120 days or accept that Q1 only detects a larger effect, and lead with Q2.

If randomising by clinic day, inflate n by the design effect (1 + (m − 1)·ICC), where m is appointments per clinic day and ICC is the intra-day correlation. ICC is unknown before the baseline; the statistician sets it.

## 5. What counts as a recovered slot

From `04_business_case.md`. A slot counts as **billable recovered** only if **all** hold:
1. it was freed (cancellation by the patient or release by staff, never a predicted no-show);
2. the agent filled it, as recorded in the ledger (`offer` → `accept` → `filled`);
3. the patient **attended** (`attended` event, taken from the hospital's own attendance record);
4. it **matches the hospital's booking record** in the daily reconciliation.

Billable recovered slots = treatment-arm recovered slots − (control-arm refill rate × treatment-arm freed slots).

Simulated reference only: on the synthetic showcase day the agent recovered <!--m:recovered_slots-->14<!--/m--> slots, of which <!--m:billable_recovered_slots-->9<!--/m--> are billable under this definition (SIMULATED, with a synthetic attendance event).

## 6. 90-day plan, week by week

**Before day 0 (weeks −6 to −1):** discovery done (`02_discovery.md`), DPIA signed by the DPO (`05b_dpia_draft.md`), processor agreement (GDPR Art. 28) signed, ENS category confirmed, works council consulted (§8), contract in place (`04_business_case.md` §procurement), waiting-list export tested, scripts reviewed by the patient advocate.

| Week | Phase | Milestones | Exit check |
|---|---|---|---|
| 1 | Set-up | Connector to the scheduling system in test; waiting-list export daily; agent configs pushed in `production-reference` profile; kill switch tested by admissions and IT | IT and DPO sign the go-live checklist |
| 2 | Shadow | Agent runs against real schedules **without calling**: it proposes calls and backfill offers, staff compare with what they would do | No list-order deviation; proposals match staff judgement on sampled cases |
| 3 | Soft launch | Calls to a small share of treatment-arm appointments (confirm/cancel only), working hours, admissions team listening to a daily sample | Zero privacy incidents; handoff queue manageable |
| 4 | Ramp | Full treatment arm for confirm/cancel; backfill switched on | Webhook error < 5%; reconciliation runs daily with no unexplained mismatches |
| 5–6 | Steady state | Weekly review with head of admissions; first interim safety report to DPO | Safety criteria held for 2 weeks |
| 7 | Add reschedule | Reschedule flow (atomic swap) switched on | No double bookings; no patient left without an appointment |
| 8 | Mid-point review | Interim numbers to the director (labelled interim); patient advocate reviews complaints and transcripts sample | Continue / adjust / stop |
| 9–11 | Steady state | Languages beyond Spanish if the baseline shows demand; staff survey | — |
| 12 | Close | Last calls; final reconciliation | Data frozen |
| 13 | Readout | Analysis per the pre-registered plan; executive readout (`readout/es/`) | Go / no-go decision (§7) |

The analysis plan (primary outcome, test, exclusions) is written down and shared with the director's office **before week 1**, so nobody picks the metric after seeing the results.

## 7. Go / no-go, kill switch and stop-loss

### Go / no-go at day 90

| Criterion | Go if | Source |
|---|---|---|
| Privacy | **Zero** confirmed disclosures of health data to anyone other than the verified patient | Incident log, DPO review |
| List order | **Zero** offers made out of the hospital's list order | Ledger verifier against list snapshots |
| Recovered slots | Billable recovered slots above the threshold the director set before launch | Reconciliation |
| Cost | Cost per billable recovered slot below the value threshold agreed in the business case | `04_business_case.md` formulas |
| Acceptance | Opt-out and complaint rates below thresholds agreed with the patient advocate | Hospital patient services |
| Operations | Admissions team can run the exceptions queue within current staffing | Head of admissions |

Thresholds are set by the hospital **before** launch and written into the pilot contract (`04b_tender_spec.md` §acceptance). We don't propose numbers we haven't measured.

### Kill switch

- One control on the console (access code required, every use logged with who and when). It stops new calls immediately; calls in progress finish their current sentence and close with the callback number.
- Who may press it: head of admissions, the on-call IT lead, the DPO, the vendor's deployment lead.
- Restart needs two of those four.
- Tested in week 1 and again at the mid-point.

### Stop-loss (automatic pause, then human review)

| Trigger | Action |
|---|---|
| Any suspected privacy leak flagged by the leak detector or by a patient | Pause all calls; DPO reviews within one working day |
| An offer out of list order detected by the verifier | Pause backfill; IT and admissions review the list export |
| Transfers to a human spike above the agreed daily ceiling | Pause new campaigns; review transcripts |
| Webhook error rate above 5% over an hour | Pause new calls; fall back to SMS only |
| A complaint escalated to the patient services unit about the agent's conduct | Review within 48 hours; pause if pattern |
| Calling outside Mon–Sat 09:00–20:00 Europe/Madrid | Pause; this should be impossible, so treat as an incident |

## 8. Staffing and change management

**Admissions team: from dialling to handling exceptions.** The agent makes the routine calls. Clerks handle what needs a person: patients who ask for a human, failed identity checks, bereavement, guardianship, interpreters, complex reschedules and anything clinical. The exceptions queue shows a short summary and a one-click callback.

| Who | What changes | Support |
|---|---|---|
| Admissions clerks | Fewer outbound reminder calls; own the exceptions queue | 2 × 1-hour sessions (console, exceptions, kill switch); listen to 10 sample calls together |
| Head of admissions | Weekly review, kill-switch holder | Weekly 30-minute review with the deployment lead |
| IT | Owns the connector and the export | Runbook (`10_operations.md`), on-call rota agreed |
| DPO | Reviews safety reports | Interim report at week 6 and week 13 |
| Clinicians in the pilot specialty | No change to clinics except fuller days | Briefing note; route for clinical questions patients raise |

**Works council (*comité de empresa* / staff representatives).** Consult before launch, not after:
- The pilot is framed as capacity for work that isn't being done today (backfill), not as replacing posts. No post is removed during the pilot.
- The dashboard does not measure individual staff performance. Console actions are logged for audit (kill switch, callbacks), not for productivity tracking.
- A staff representative joins the mid-point review.

**Patients.**
- Every call opens with the AI disclosure and the recording notice (`06_conversation_design.md`).
- The hospital's website and SMS carry a short note: "You may get a call from the hospital's automated assistant to confirm your appointment. You can ask for a person at any time."
- Opt-out is honoured on the call and recorded; opted-out patients get SMS only.
- The patient advocate reviews scripts before launch and a transcript sample at mid-point.

## 9. Scale path

| Step | Scope | What changes | Procurement |
|---|---|---|---|
| 1 | Pilot: one specialty, one site | As above | Minor contract or innovation route (`04_business_case.md`) |
| 2 | Whole hospital | More specialties and sites; more concurrent calls; reschedule across sites; languages per baseline; inbound cancellations (patients call in, cancellation triggers backfill at once) | Open or simplified open procedure, paying per verified recovered slot |
| 3 | Regional health service | Multiple hospitals; one connector per scheduling system or a regional integration engine; FHIR R4 where available; regional reporting | Framework agreement or regional tender; the tender spec in `04b_tender_spec.md` is written to scale to lots |

**What has to be true before step 2:** go criteria met, EU data residency and zero-retention settings confirmed for production (Enterprise features on the platform, see `05_solution_design.md` §demo vs production), and a concurrency plan. In production with zero retention, calls are placed one at a time rather than through batch calling (`docs/DECISIONS.md`), so throughput per agent line has to be sized against the daily call volume.

## 10. Risks to the pilot itself

| Risk | Mitigation |
|---|---|
| Waiting list export is stale (patient already seen, or deceased) | Daily export; agent checks status at call time; staff remove flagged entries; any such call is an incident |
| Baseline no-show rate lower than expected | Lead with Q2 (backfill), which doesn't depend on a large no-show reduction |
| Contamination between arms (clerks change behaviour) | Randomise by clinic day; log staff backfill calls in both arms |
| Speech recognition fails on elderly patients | Spelled-out digits fallback; two failed identity checks → callback message; track identity-failure rate by age band |
| Patients distrust an automated call from the hospital | Callback number they can check against the hospital's published number; SMS mentions the call |

---

## Sources

Source IDs match `01_account_brief.md`; full list in `research/sources.md`.
- **[S2]** Jabalera Mesa (2015), doctoral thesis, data 2013–14; literature review on SMS and phone reminders (secondary citations).
- **[S5]** Galicia region, 2024 figures, press report of 28 Jan 2025.
- **[S6]** Pereira-Victorio et al. (2016), data Aug 2011.
