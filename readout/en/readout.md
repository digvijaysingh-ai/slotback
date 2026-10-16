---
marp: true
theme: default
paginate: true
lang: en
title: "Slotback · Pilot proposal"
footer: "Fictional hospital · synthetic data · simulated results are labelled"
style: |
  section { font-family: "IBM Plex Sans", sans-serif; background: #FBFAF7; color: #1B1A17; font-size: 26px; }
  h1, h2 { color: #1B1A17; font-weight: 600; }
  strong { color: #1F5FA8; }
  code, .num { font-family: "IBM Plex Mono", monospace; }
  .sim { background: #FFE7A8; color: #6B4A00; font-family: "IBM Plex Mono", monospace; font-size: 16px; padding: 2px 6px; border-radius: 2px; }
  .bench { border: 1px solid #3D5A78; color: #3D5A78; font-family: "IBM Plex Mono", monospace; font-size: 16px; padding: 1px 6px; border-radius: 2px; }
  .synth { border: 1px solid #5E5A52; color: #5E5A52; font-family: "IBM Plex Mono", monospace; font-size: 16px; padding: 1px 6px; border-radius: 2px; }
  .care { border: 1px solid #1F6F60; color: #1F6F60; font-size: 18px; padding: 1px 6px; border-radius: 2px; }
  table { font-size: 22px; }
  footer { font-size: 14px; color: #5E5A52; }
---

# Recovered slots, not reminders

**A 90-day pilot proposal for outpatient clinics**
Hospital General (fictional) · Director's office

A voice agent that confirms appointments and offers freed slots to the waiting list, **in the order the hospital sets**.

<span class="sim">SIMULATED</span> Every Slotback result in this deck comes from a synthetic clinic day. No real pilot has run yet.

---

## 1 · The problem: consultations nobody uses

| Benchmark (other regions) | Figure | Source |
|---|---|---|
| One health area, outpatient clinics | **13.8%** of 400,761 appointments missed; **≈ €3.39M** | <span class="bench">BENCHMARK [S2, 2013–14]</span> |
| Valencia region, specialist clinics | **9.7%**: 733,580 of 7.56M | <span class="bench">BENCHMARK [S1, 2014]</span> |
| Galicia region, hospital outpatient | **5.75%**: 245,535 missed | <span class="bench">BENCHMARK [S5, 2024]</span> |

- Average cost of a missed appointment: **≈ €61** <span class="bench">BENCHMARK [S2, 2013–14]</span> (our calculation).
- For Hospital General (fictional): 380,000 appointments a year at a 12% no-show rate → **≈ 45,600 empty slots** <span class="synth">SYNTHETIC</span>

---

## 2 · Why patients miss appointments

- **29.6%** forgot; **16%** communication failure → **46%** combined <span class="bench">BENCHMARK [S2, 2013–14]</span>
- Non-attenders are somewhat younger (51.3 vs 55.7 years) and waited longer from booking (25.2 vs 19.2 days) <span class="bench">[S2]</span>. Associations, not predictions.
- Phone lines for cancelling are saturated; a regional ombudsman notes the elderly and rural patients are hit hardest <span class="bench">[S3, 2021]</span>.

**What already works:** SMS is the most cost-effective fix for forgetting [S2]. We don't propose replacing it.

---

## 3 · What SMS can't do

| | SMS | SMS + voice agent |
|---|---|---|
| Remind | ✓ | ✓ |
| Cancel or change the appointment in the same contact | ✕ | ✓ |
| Offer the freed slot to the next patient on the list **today** | ✕ | ✓ |
| Catch out-of-date phone numbers [S5] | ✕ | ✓ |
| Reach people who don't read SMS or prefer to talk | ✕ | ✓ |

The value isn't "a better reminder". It's **turning a no-show into an early cancellation, and that cancellation into an appointment for someone else.**

---

## 4 · How it works

1. **3–5 days ahead**, the agent calls. It says it's an automated assistant, gives the recording notice and **verifies identity** (date of birth + part of the ID number) before saying anything, not even the specialty.
2. The patient **confirms, cancels or reschedules**. The agent reads back what was agreed.
3. When a slot frees up, the agent calls the waiting list **strictly in the hospital's order**, holding the slot for 10 minutes per offer.
4. Voicemail or a relative: **only a callback number**, no health details.
5. Any clinical question, request for a person or sensitive case → **admissions staff**.

<span class="care">◆ AI disclosed</span> <span class="care">◆ identity verified</span> <span class="care">◆ read back</span> <span class="care">◆ handed to a human</span>

---

## 5 · Results on the synthetic day

<span class="sim">SIMULATED</span> Synthetic clinic day: 5 specialties, 400 appointments, 60 patients per waiting list. Not real results.

| Indicator | Value |
|---|---|
| Recovered slots | <!--m:recovered_slots-->14<!--/m--> <span class="sim">SIMULATED</span> |
| Of which billable (attended + matches hospital booking − SMS baseline) | <!--m:billable_recovered_slots-->9<!--/m--> <span class="sim">SIMULATED</span> |
| Fill rate of freed slots | <!--m:fill_rate-->100%<!--/m--> <span class="sim">SIMULATED</span> |
| Median time to fill (min) | <!--m:median_time_to_fill_min-->11.0<!--/m--> <span class="sim">SIMULATED</span> |
| Privacy leaks in <!--m:eval_scenarios_total-->15<!--/m--> test conversations | <!--m:privacy_leaks-->0<!--/m--> <span class="sim">SIMULATED</span> |
| Cost per recovered slot (€) | <!--m:cost_per_recovered_slot_eur-->€3.54<!--/m--> <span class="sim">SIMULATED</span> |

Every slot is written to a **hash-chained ledger** with a signed daily head handed to the hospital. The hospital's booking system stays the source of truth.

---

## 6 · Risks and controls

| Risk | Control |
|---|---|
| Health data disclosed to someone else | Identity before any detail; voicemail and third parties get a callback number only; leak detector, zero tolerance |
| AI deciding who is seen first | **Never prioritises.** Offers in the hospital's list order; slots are freed only by cancellation or by staff. Outside AI Act Annex III |
| Clinical advice | Forbidden; routes to a person or to 112 |
| Older patients reject it | Slower pace, spell-out option for digits, a person always available |
| Something goes wrong in production | **Kill switch** on the console, logged with who and when; automatic pauses on thresholds |

Legal basis: GDPR Art. 6.1.e and 9.2.h, LOPDGDD, Ley 41/2002. Processor agreement (Art. 28), DPIA (Art. 35), ENS. AI Act Art. 50 transparency (application date: to verify).

---

## 7 · The pilot: 90 days, one specialty

- **One specialty** with a high no-show rate and a waiting list that can be exported in order.
- **Control:** SMS only (today's process). **Treatment:** SMS + voice agent. Assigned by clinic day.
- Week 2 in **shadow mode** (proposes, doesn't call); week 3 soft launch; reschedule from week 7.
- Analysis plan fixed **before** launch.

| Day-90 decision | Continue if… |
|---|---|
| Privacy | Zero confirmed disclosures |
| List order | Zero out-of-order offers |
| Billable slots | Above the threshold the director sets |
| Acceptance | Opt-outs and complaints below the threshold agreed with patient services |

---

## 8 · Commercial proposal and procurement route

**Pay per verified recovered slot**: filled by the agent, **attended by the patient**, **matched to the hospital's booking record**, minus what the SMS arm would have filled anyway.

| Option | Risk to the hospital | Risk to the vendor |
|---|---|---|
| Per minute | High: pays even without results | Low |
| Per verified recovered slot, capped | Low | High (**recommended for the pilot**) |
| Small fixed fee + per-slot fee | Moderate | Moderate (**recommended at scale**) |

**Route:** preliminary market consultation → **minor contract** for the pilot (services < €15,000 excl. VAT, LCSP 9/2017) → open procedure or innovation partnership to scale. Draft tender spec available.

---

## 9 · What we're asking for

1. **Approve the 90-day pilot** in one specialty, with SMS as the control arm.
2. **Name** the head of admissions as service owner.
3. **Start the DPIA review** with the DPO, and **consult the works council** before launch.
4. **Ask IT** for a daily export of the waiting list in its official order.
5. **Set the day-90 thresholds** before launch.

Next step: a 45-minute meeting with admissions, IT and the DPO within two weeks.

---

## Sources

All checked against the original documents on 16 Oct 2026. Institutions are described generically.

- **[S1]** Press report on specialist no-shows, Valencia region, Jan–Nov 2014 (published 30 Jan 2015).
- **[S2]** Jabalera Mesa, M.L. (2015). *Factores determinantes del absentismo en consultas externas*, doctoral thesis, data 2013–14 (Tables 26, 29, 46).
- **[S3]** Regional ombudsman resolution, case file 1259/2021 (primary care).
- **[S5]** Press report on no-shows in the Galicia region in 2024 (published 28 Jan 2025).

Detail: `docs/01_account_brief.md` and `research/sources.md`. Slotback results: `metrics/registry.json`, all **SIMULATED**.
