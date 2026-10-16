# Memo to the hospital director · Slotback pilot

**To:** Director, Hospital General (fictional)
**Subject:** 90-day pilot of a voice agent that confirms outpatient appointments and recovers freed slots
**Date:** 16 Oct 2026
**Note:** fictional hospital, synthetic data. Public figures are benchmarks from other regions, with source and year. Slotback results are **SIMULATED**: no real pilot has run.

---

**1. Problem.** Elsewhere in Spain, 5.75% to 14.6% of specialist outpatient appointments are missed (Galicia 2024 [S5]; one tertiary hospital, 2011 [S6]). In the best-documented health area it was 13.8%, about €3.39M a year and about €61 per missed appointment (doctoral thesis, data 2013–14 [S2]). 46% of non-attenders said they forgot or there was a communication failure [S2]. On the hospital's synthetic profile (380,000 appointments, 12%), that is about 45,600 empty slots a year (SYNTHETIC).

**2. Proposal.** A voice agent that calls 3–5 days before the appointment to confirm, cancel or reschedule, and offers each freed slot to the waiting list **in the hospital's own order**, holding it for 10 minutes per offer. It doesn't replace SMS, which is the cheapest fix for forgetting [S2]. It does what SMS can't: take the cancellation and give the slot to another patient before the day.

**3. Safeguards.** It says it is an automated assistant and that the call is recorded. It verifies identity before giving any detail, including the specialty. On voicemail or with a third party it leaves only a callback number. It never gives clinical advice and never decides priority; slots are freed only by a cancellation or by staff, which keeps it outside the AI Act's Annex III. Patients can always ask for a person or opt out. The console has a kill switch.

**4. Simulated results.** On a synthetic clinic day (5 specialties, 400 appointments): <!--m:recovered_slots-->14<!--/m--> slots recovered, <!--m:billable_recovered_slots-->9<!--/m--> billable, and <!--m:privacy_leaks-->0<!--/m--> privacy leaks across <!--m:eval_scenarios_total-->15<!--/m--> test conversations. All **SIMULATED**. They show the method, not a promised result.

**5. Pilot.** 90 days in one high no-show specialty. Control arm SMS only; treatment arm SMS + voice, assigned by clinic day. Shadow mode in week 2. Continue only with zero data disclosures, zero out-of-order offers, and billable recovered slots above a threshold the director sets before launch.

**6. Price and procurement.** Pay per **verified recovered slot**: filled by the agent, attended by the patient, matched to the hospital's booking record, minus what the SMS arm would have refilled anyway. Total capped to fit a **minor contract** (*contrato menor*, services < €15,000 excl. VAT, LCSP 9/2017). To scale: open procedure or innovation partnership.

**7. Decisions requested.** (a) Approve the pilot. (b) Name the head of admissions as service owner. (c) Start the DPIA review with the DPO and consult the works council. (d) Ask IT for a daily, ordered waiting-list export. (e) Set the day-90 thresholds.

---

*Sources: [S2] Jabalera Mesa (2015), doctoral thesis, data 2013–14; [S5] press report on Galicia, 2024 data; [S6] Pereira-Victorio et al. (2016), 2011 data. Detail in `docs/01_account_brief.md`.*
