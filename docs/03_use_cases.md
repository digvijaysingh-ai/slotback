# 03 · Use-case prioritisation

**Account:** a regional public health service in Spain · *Hospital General (fictional)*.
**Question:** of six voice-agent candidates, which one goes first?
**Answer:** **outbound appointment confirmation, combined with waiting-list backfill**, as one loop. Triage is excluded.

Scores are our pre-discovery judgement, to be revisited once the baseline from `02_discovery.md` comes in.

---

## 1. Scoring method

Each candidate is scored 1–5 on three criteria. Risk is scored so that **5 = lowest risk**, so higher is always better.

| Criterion | Weight | What a 5 looks like |
|---|---|---|
| **Value** | 40% | Directly reduces empty slots or waiting time; measurable in a 90-day pilot; differentiated from what the hospital already has |
| **Feasibility** | 30% | Narrow integration (a few read/write calls), short scripted conversations, works with today's data |
| **Risk** (inverted) | 30% | No clinical content, minimal health-data exposure, low reputational and regulatory exposure |

Weighted score = 0.4 × Value + 0.3 × Feasibility + 0.3 × Risk.

## 2. Candidates

| # | Use case | Value | Feasibility | Risk (5 = low) | Weighted | Decision |
|---|---|---|---|---|---|---|
| 1 | **Outbound confirm / cancel / reschedule** | 5 | 4 | 4 | **4.4** | **Pilot** |
| 2 | **Waiting-list backfill** | 5 | 3 | 4 | **4.1** | **Pilot (with #1)** |
| 3 | Inbound booking | 3 | 3 | 4 | 3.3 | Later phase |
| 4 | Prep instructions | 2 | 4 | 3 | 2.9 | Bolt-on after pilot |
| 5 | Results delivery | 2 | 2 | 1 | 1.7 | Not recommended |
| 6 | Triage | — | — | — | — | **Excluded** |

### 1. Outbound confirm / cancel / reschedule: 4.4
- **Value 5.** Targets the top stated reason for no-shows (forgetting, 29.6% [S2]) and the second (communication failure, 16% [S2]). Turns silent no-shows into early cancellations, which is what makes backfill possible. Also catches record errors such as duplicate bookings, appointments the patient never heard about, or ones already cancelled. Together these made up 47% of reasons in another study [S6]. Reaches elderly patients that apps and SMS links miss.
- **Caveat:** for forgetting alone, SMS is about as effective as a call and 15–35% cheaper (trials cited in [S2]). The confirmation call earns its place because it's two-way and feeds backfill, not as a stand-alone reminder. That's why the two go together.
- **Feasibility 4.** Short, structured conversation. Needs read appointment, confirm, cancel and (optionally) list alternative slots. Reschedule adds a write call and more dialogue paths; it can be phased in after confirm/cancel.
- **Risk 4.** Health data is involved (even the specialty), so identity must be verified before any detail, and voicemail gets a callback number only. No clinical content.

### 2. Waiting-list backfill: 4.1
- **Value 5.** This is where *recovered slots* comes from, the headline metric and the basis for outcome-based pricing. Also shortens waits for the people on the list.
- **Feasibility 3.** Needs the waiting list exported in its official order, kept current, and a booking write call. Time-boxed calling logic (stop when the slot is too close to fill). Data quality of the list is the main unknown.
- **Risk 4.** The agent **never decides priority**: it offers slots strictly in the hospital's list order. That keeps it out of AI Act Annex III high-risk territory (AI deciding access to public healthcare). A stale list (patient already seen, deceased) is the main reputational risk, handled by checks in discovery and at call time.

**Why #1 and #2 go together:** confirmation creates the freed slots; backfill fills them. Alone, confirmation reduces no-shows but leaves cancelled slots empty; alone, backfill has few early cancellations to work with. Together they form one loop with one metric.

### 3. Inbound booking: 3.3
- **Value 3.** Relieves saturated phone lines, a real and documented problem (waits of up to 45 minutes in one 2021 ombudsman case, though that case was in primary care) [S3]. But it doesn't recover empty slots by itself, and ElevenLabs already publishes an inbound scheduling tutorial [S4], so it's not a differentiated showcase.
- **Feasibility 3.** Open-ended caller intents, wider integration surface (search availability across specialties, referrals).
- **Risk 4.** Same identity and data rules as above; callers are more likely to drift into clinical questions.
- **Decision:** natural second phase once the scheduling connector from the pilot exists. Handling inbound "I want to cancel" calls fits early, since it feeds backfill.

### 4. Prep instructions: 2.9
- **Value 2.** Some no-shows and wasted visits come from patients arriving unprepared (fasting, bringing tests). Real but narrower, and specialty-specific.
- **Feasibility 4.** Read-only, scripted content.
- **Risk 3.** The content is clinical, even if scripted. Every script needs clinical sign-off, and patients will ask follow-up questions the agent must not answer.
- **Decision:** add as an optional segment of the confirmation call once scripts are approved per specialty.

### 5. Results delivery: 1.7
- **Value 2.** Saves clinician and admin time, but doesn't touch no-shows or waiting lists.
- **Feasibility 2.** Requires access to clinical results systems and a clinician-approved message for each result type.
- **Risk 1.** Delivering results is clinical communication. An abnormal result or a misheard question is a patient-safety and reputational event. Highest health-data exposure of any candidate.
- **Decision:** not recommended. At most, a "your results are ready, please book a review" notice with no content, and only after the core loop is proven.

### 6. Triage: excluded
- Deciding urgency or which care a patient needs is clinical judgement, and AI that affects access to public healthcare falls into the AI Act Annex III high-risk category.
- Excluded regardless of score. Any triage-like question during a call ("should I go to A&E?") is escalated to a human or emergency number, per the guardrails in phase 5.

## 3. Recommendation

**Pilot:** outbound confirmation (confirm/cancel first, reschedule in the second month) plus waiting-list backfill, in one high no-show specialty, compared against SMS-only reminders (plan in phase 8).

**Headline metric:** recovered slots = freed slots refilled by the agent + no-shows avoided vs the control arm.
The first term is counted call by call from the booking log, so it can be billed (outcome-based pricing, phase 4). The second is a statistical estimate from the pilot comparison and is reported, not billed.

**Supporting metrics:** contact rate, confirmation rate, early-cancellation rate, backfill fill rate and time-to-fill, escalations to staff, privacy incidents (target: zero).

**Sequencing after the pilot:** inbound cancellations → prep-instruction segment → full inbound booking. Results delivery and triage stay out of scope.

## 4. What would change this ranking

- **No usable export of the waiting list in order** → backfill drops to feasibility 1–2; pilot starts with confirmation only and backfill follows once IT builds the export.
- **Very low share of valid phone numbers** → value of every outbound use case falls; fix data first.
- **Hospital already runs effective two-way SMS with high response** → value of #1 falls; backfill becomes the lead.
- **Inbound abandonment rate is extreme** → inbound cancellations move up into the pilot.

---

## Sources

- **[S2]** Jabalera Mesa, M.L. (2015). *Factores determinantes del absentismo en consultas externas* [doctoral thesis], data 2013–14: https://riuma.uma.es/entities/publication/5e36d04e-e88f-4e25-9cc2-c6a623d0127f
- **[S3]** Regional ombudsman resolution, case file 1259/2021, on phone access to a primary-care health centre: https://procuradordelcomun.org/archivos/resoluciones/1_1620373534.pdf
- **[S4]** ElevenLabs, "ElevenAgents for Healthcare: Build a scheduling agent" (13 Aug 2026): https://elevenlabs.io/blog/elevenagents-for-healthcare-build-an-inbound-appointment-scheduling-agent
- **[S6]** Pereira-Victorio et al. (2016). *Medicina General y de Familia* 5:83–90. DOI 10.1016/j.mgyf.2016.02.002

Source IDs match `01_account_brief.md`. Full list: `research/sources.md`.
