# 01 · Account brief

**Account:** a regional public health service in Spain, piloting at *Hospital General (fictional)*.
**Use case under evaluation:** outbound voice agent that confirms, cancels or reschedules specialist appointments, and offers freed slots to the waiting list in the hospital's own order.
**Status:** pre-discovery. Everything below about the fictional hospital is a hypothesis to test in discovery (`02_discovery.md`). Public figures are real, published benchmarks from other regions, each with its source and year. All were re-checked against the original documents on 2026-10-16.

---

## 1. The problem in one paragraph

Patients miss specialist outpatient appointments (*absentismo*). In the best-documented Spanish case, a public health area with three hospital sites lost **55,249 of 400,761 appointments (13.8%)** in a year, at a cost of **€3.39M** [S2]. The top reason patients gave was simply that they forgot (29.6%), followed by communication failures between the system and the patient (16%) [S2]. One regional health service reached the same diagnosis in 2015 and announced a plan to phone patients to "confirm appointments and reassign the slots that may be freed" [S1]. That is exactly the loop this project automates. Meanwhile the phone lines patients would use to cancel are saturated, and a regional ombudsman has recorded that elderly, rural and vulnerable people are hit hardest [S3].

## 2. Problem sizing: real cases (other regions)

### 2.1 Reference case: Costa del Sol health area (Andalusia), data 2013–14

This is the anchor for the business case: the only Spanish source we found with appointment volume, missed appointments, cost **and** patient-reported reasons all from the same population. Source: doctoral thesis [S2], with the case-control study published in a journal in 2015 [S2b] and the cost analysis in 2017 [S2c].

| Site type | Appointments | Missed | No-show rate | Cost of missed appointments |
|---|---|---|---|---|
| General hospital | 256,377 | 36,355 | 14.18% | €2,475,640 |
| High-resolution hospital | 44,848 | 5,468 | 12.19% | €515,936 |
| High-resolution specialty centre | 99,536 | 13,426 | 13.49% | €395,342 |
| **Total** | **400,761** | **55,249** | **13.79%** | **€3,386,919** |

*Source: [S2], Table 46. The missed appointments are 14% of the area's total outpatient cost of €24.2M.*

- **Cost per missed appointment: ≈ €61** (our calculation: €3,386,919 ÷ 55,249). This average hides a wide spread between sites: about €29 per missed appointment at the specialty centre, €68 at the general hospital and €94 at the high-resolution hospital (our calculation from the per-site figures above).
- Rebooking a missed appointment cost an extra **€12.95** on average [S2c].

**Why patients said they didn't attend** (294 non-attenders, telephone survey) [S2, Table 26]:

| Reason | Share |
|---|---|
| Forgot | **29.6%** |
| Communication failure (between the system and the patient) | **16.0%** |
| Got better | 4.8% |
| Physical incapacity | 3.7% |
| Administrative error | 3.4% |
| Dissatisfaction | 2.4% |
| Tests not ready | 1.0% |
| Other reasons | 39.1% |

So about **46% of no-shows came from forgetting or a communication failure**. A two-way reminder call addresses both directly.

**Who misses appointments** (case-control, 294 cases vs 588 controls) [S2, Table 29]:
- No-shows were younger: mean age **51.3 vs 55.7** years (p < 0.001). The study concludes that younger patients who rarely attend clinics are the highest-risk group.
- No-shows had waited longer: mean booking delay **25.2 vs 19.2 days** (p = 0.048). The journal abstract states that "a shorter time period before the appointment and older age were significantly associated with fewer absences, as well as the fact of having attended more consultations in the past year" [S2b].
- No-shows had attended clinics less often in the previous year: **3.6 vs 4.8** visits (p < 0.001).
- Sex and distance to the centre were not significant.

### 2.2 Other real benchmarks

| Setting | Figure | Period | Source |
|---|---|---|---|
| Valencia region, all specialist outpatient appointments | 7,563,513 appointments, **733,580 missed = 9.7%**; average outpatient wait 38 days | Jan–Nov 2014 | [S1] |
| Galicia region, hospital outpatient appointments | **245,535 missed**; no-show rate down from **8.58% (2017) to 5.75% (2024)** | 2024 | [S5] |
| Galicia region, in-person primary care | 3.86% (≈ 702,504 missed) | 2024 | [S5] |
| Tertiary hospital in Castilla-La Mancha, new specialist appointments | **14.6%** (276 of 1,885) | one week, Aug 2011 | [S6] |

**Reading the range honestly**
- Specialist no-show rates in Spain run from about **6% to 14%** depending on the region, the year and whether follow-up visits are counted. The lowest recent figure (Galicia, 5.75% in 2024) shows that rates can fall. The hospital's own baseline is what counts, so we measure it in discovery and don't assume a rate.
- Even at the low end, absolute volumes are large: a quarter of a million missed hospital appointments in one region in a single year [S5].
- In the Castilla-La Mancha study, the largest single reason was "didn't know about the appointment" (16.1%). Next came "had a duplicate appointment or went on another date" (15.6%), "had already cancelled" (15.1%), "forgot" (12.9%) and "got better" (12.4%) [S6]. Several of these are record-keeping and communication failures, not patient behaviour, and a confirmation call catches them before the day.

### 2.3 What has been tried: reminder evidence

From the literature review in [S2] (secondary citations; we have not re-read the original trials):

| Intervention | Effect reported | Original study |
|---|---|---|
| Phone reminder, adolescents | no-show rate **20% → 8%** | Sawyer et al., 2002 |
| Phone reminder, urban US population | **26% → 19%** | Hashim et al., 2001 |
| Phone reminder, elderly patients (UK) | **5-point** reduction | Dockery et al., 2001 |
| SMS vs phone reminder | equally effective | Liew et al., 2009 |
| SMS vs phone reminder, cost | SMS **15–35% cheaper** per patient | Leong et al., 2006; Chen et al., 2008 |

**Implication for the pitch.** The reference study itself concludes that SMS is the most cost-effective fix *for forgetting* [S2]. So we don't sell voice as "a better reminder than SMS". The case for voice is what SMS can't do:
1. **Two-way:** the patient can cancel or reschedule there and then, which frees the slot early.
2. **Backfill:** a freed slot is offered straight away to the next person on the hospital's list. Recovered slots are the outcome SMS can't produce.
3. **Reach:** SMS to outdated numbers often never arrives, a problem a regional GP society raised in 2025 [S5]. Elderly patients are also less likely to act on a text link.
4. **Staff capacity:** the regional plan in [S1] relied on phone calls, which is exactly the work admissions staff can't scale.

The pilot (phase 8) compares voice against SMS-only for this reason.

### 2.4 Phone-line saturation

A regional ombudsman resolution from 2021 [S3] upheld a complaint about phone access to a primary-care health centre. Calls kept dropping, the patient's details were taken twice, and getting through could take **up to 45 minutes**. The ombudsman noted that phone-access problems had been constant since the start of the pandemic and had been "even greater for elderly people, those living in rural areas or especially vulnerable". The case concerns primary care, not hospital admissions. We use it only as evidence that saturated lines and their impact on the elderly are on the public record.

### 2.5 Sizing for Hospital General (fictional)

The fictional hospital has its **own synthetic profile**. It deliberately does not copy the reference area's figures, so it can't be mistaken for a real institution. It is calibrated to sit inside the published range, and every cost figure is still traced to a real benchmark:

| Input | Value | Type | Basis |
|---|---|---|---|
| Specialist outpatient appointments per year | 380,000 (3 sites) | SYNTHETIC | Chosen to be comparable in size to the reference case [S2] (400,761) |
| No-show rate | 12% (sensitivity: 5.75% – 14.6%) | SYNTHETIC | Inside the published range [S5], [S6]; reference case 13.8% [S2] |
| Missed appointments per year | 45,600 (sensitivity: ≈ 21,850 – 55,480) | SYNTHETIC | 380,000 × 12% (range: × 5.75% / 14.6%) |
| Cost per missed appointment | ≈ €61 | BENCHMARK [S2, 2013–14] | €3,386,919 ÷ 55,249, our calculation |
| Annual cost of missed appointments | ≈ €2.80M | SYNTHETIC × BENCHMARK | 45,600 × €61.30 |
| Share of no-shows from forgetting or communication failure | 46% | BENCHMARK [S2, 2013–14] | Table 26 |

The demo uses one synthetic clinic day: 5 specialties, 400 appointments, 60 patients on each waiting list. It is generated deterministically by `slotback/data/generate.py`.

What we **don't** assume: how many of those no-shows a voice agent prevents, or how many freed slots it refills. Those numbers come from the pilot (phase 8), compared against SMS-only. The ROI model (phase 4) takes them as inputs, with the trial results in §2.3 as a sanity range only.

## 3. Why now: buying triggers

1. **Waiting lists are on the political agenda.** Regional health services publish waiting-list figures per hospital and department, and those figures get press and parliamentary attention. In one region, delay in specialist care was the top cause of written patient complaints: 25.1% of 14,254 in 2013 [S1]. *Recovered slots* is a number a hospital director can report upward.
2. **The fix is already policy, but staff can't scale it.** A regional health service announced phone confirmation and slot reassignment as its answer to no-shows [S1]. The constraint is staff time, not the idea.
3. **Phone-line saturation is on the record** [S3]. Taking routine outbound work off staff frees inbound capacity.
4. **AI Act transparency rules (Art. 50) apply from 2 Aug 2026.** Buyers now need vendors who disclose AI use by design. Arriving with that built in is a differentiator. (Confirm current application status before relying on it in a proposal.)
5. **Budget and procurement cycle.** A small pilot can go through a minor contract or innovation-procurement route before a full tender (detail in phase 4).
6. **SMS reminders already exist in many services,** but phone numbers on file are sometimes out of date [S5]. That gives a ready comparison arm for the pilot and an argument for checking numbers by calling them.

## 4. Stakeholder map

| Stakeholder | Role in the deal | What they care about | Likely concern | What wins them |
|---|---|---|---|---|
| **Hospital director** (*gerente*) | Economic buyer, executive sponsor | Waiting-list figures, cost, reputation | Political risk if the AI gets something wrong in public | Recovered-slot metric they can report; outcome-based pricing; kill switch |
| **Head of admissions** (*jefe/a de admisión*) | Champion, day-to-day owner | Staff workload, fewer empty slots, fewer complaints | Another system to babysit; who handles the exceptions | Agent does the volume, staff handle escalations; dashboard of what happened |
| **IT / information systems** | Technical gatekeeper | Integration with the scheduling system (HIS), security, support burden | Write access to the scheduling system; vendor lock-in | Narrow API (read slot, confirm, cancel, offer, book), audit log, ENS alignment |
| **Data protection officer** (DPO, *DPD*) | Veto holder | GDPR Art. 9 health data, DPIA, processor terms | Health data disclosed to the wrong person; data leaving the EU | Identity check before any detail; no health data on voicemail; EU residency; zero retention; DPA under Art. 28 |
| **Works council** (*junta de personal / comité de empresa*) | Must be consulted | Job security, workload, monitoring of staff | "Automation to cut posts" | Framed as capacity for unmet work; staff stay in the loop for every escalation; no staff performance monitoring |
| **Patient advocate** (patient services unit, patient associations) | Influencer, reputational check | Accessibility, elderly and non-Spanish speakers, right to a human | Patients confused or pressured by a machine | AI disclosure up front; human handoff on request; opt-out; language support |
| **Clinical heads of service** | Influencer | Clinic utilisation, no clinical risk | Agent drifting into clinical questions or reordering priority | Agent never gives clinical advice and never changes the list order |
| **Procurement** (*contratación*) | Process owner | Legal route, value thresholds, tender rules | Directly awarding to a vendor | Pilot sized for a minor contract; clear path to an open tender |

**Coalition to build first:** head of admissions (champion) + DPO (earliest possible review, not last-minute). The director signs once those two say yes.

## 5. Constraints that shape the design from day one

- **No clinical advice and no prioritisation.** Freed slots are offered strictly in the order the hospital's list provides. This keeps the system out of the AI Act Annex III high-risk category (AI deciding access to public healthcare).
- **Identity before detail.** Even the specialty is health data. Date of birth plus part of the ID number before anything is revealed.
- **Voicemail or a third party:** callback number only, no health details.
- **Legal basis is care communication, not marketing** (GDPR Art. 6.1.e and 9.2.h; LOPDGDD 3/2018; Ley 41/2002), so no marketing consent is needed. Opt-out from automated calls is still offered.
- Full compliance design in phase 5.

## 6. Competitive context

- **Status quo:** manual staff calls (effective, capacity-limited) and SMS reminders. SMS is cheap and evidence-backed against forgetting [S2], but it's one-way, can't backfill a slot, and fails on outdated numbers [S5].
- **Generic inbound booking bots:** ElevenLabs already publishes an inbound scheduling tutorial [S4], so inbound booking alone isn't differentiated. The outbound confirm + backfill loop, with recovered slots as the metric, is.
- **Call-centre outsourcing:** already bought by health services; a useful price reference for phase 4. Procurement data can show how these services are tendered, without naming any buyer.

## 7. Open questions for discovery

1. What is the hospital's current no-show rate, by specialty, age band and booking delay? Is it nearer 6% or 14%?
2. What happens to a slot freed at short notice today? How many are refilled, and how fast?
3. Which scheduling system is in use, and does it expose any API or only screens?
4. What reminder channels run today (SMS, letter, app), and with what coverage? How many SMS bounce or go to dead numbers?
5. What share of patients have a valid mobile number on file? What languages do they speak?
6. Who owns the waiting-list order, and how is it exported?
7. Has the DPO reviewed any voice or AI system before? What did they require?

---

## Sources

All checked against the original documents on 2026-10-16. Institutions are described generically in the text. Links are to the third-party publications.

- **[S1]** Press report on the Valencia region's specialist no-show figures and reminder-call plan, published 30 Jan 2015 (data Jan–Nov 2014): https://www.redaccionmedica.com/autonomias/comunitat-valenciana/20150130/el-absentismo-de-los-pacientes-en-las-consultas-se-evitara-con-recordatorios-telefonicos/335314_0.amp.html
- **[S2]** Jabalera Mesa, M.L. (2015). *Factores determinantes del absentismo en consultas externas* [doctoral thesis], data 2013–14. Abstract; Tables 26, 29 and 46; literature review on reminders. The old repository link now returns 404. Current record: https://riuma.uma.es/entities/publication/5e36d04e-e88f-4e25-9cc2-c6a623d0127f
- **[S2b]** Jabalera Mesa, Morales Asencio, Rivas Ruiz (2015). *Anales del Sistema Sanitario de Navarra* 38(2):235–245. Case-control study, 882 patients. DOI 10.4321/S1137-66272015000200007
- **[S2c]** Jabalera Mesa et al. (2017). *Revista de Calidad Asistencial* 32(4):194–199. Cost analysis. DOI 10.1016/j.cali.2017.01.004
- **[S3]** Regional ombudsman resolution, case file 1259/2021, on phone access to a primary-care health centre (2021): https://procuradordelcomun.org/archivos/resoluciones/1_1620373534.pdf
- **[S4]** ElevenLabs, "ElevenAgents for Healthcare: Build a scheduling agent" (13 Aug 2026): https://elevenlabs.io/blog/elevenagents-for-healthcare-build-an-inbound-appointment-scheduling-agent
- **[S5]** Press report on missed appointments in the Galicia region in 2024, published 28 Jan 2025, figures from the regional health service: https://www.telecinco.es/noticias/galicia/20250127/millon-consultas-perdidas-absentismo-pacientes-sanidad-gallega-2024_18_014594530.html
- **[S6]** Pereira-Victorio et al. (2016). "Absentismo de pacientes a la consulta externa especializada en un hospital de tercer nivel en España". *Medicina General y de Familia* 5:83–90. DOI 10.1016/j.mgyf.2016.02.002

Full source list: `research/sources.md`.
