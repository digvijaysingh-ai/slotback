# Sources (gathered 2026-10-16, figures re-verified against originals 2026-10-16)

## Platform
- Tests for ElevenLabs Agents: https://elevenlabs.io/blog/tests-for-elevenlabs-agents
- Simulate conversations: https://elevenlabs.io/docs/eleven-agents/guides/simulate-conversation
- ElevenLabs' own inbound healthcare scheduling tutorial, "ElevenAgents for Healthcare: Build a scheduling agent" (13 Aug 2026), so inbound booking alone is not differentiated: https://elevenlabs.io/blog/elevenagents-for-healthcare-build-an-inbound-appointment-scheduling-agent
- Customer scale (company blog): https://elevenlabs.io/it/blog/tender-22bn

## Why pilots fail
- https://ai2.work/blog/why-88-of-enterprise-ai-agent-pilots-never-reach-production
- https://www.haptik.ai/blog/why-ai-agents-dont-reach-production-and-how-voice-ai-breaks-the-pattern
  - Integration, evals, governance and ownership; the model is rarely the problem. Statistics vary by source, so treat them loosely. (Not re-verified.)

## Missed appointments (benchmarks, other regions) — verified

- **[S1] Valencia, Jan–Nov 2014** (press report, 30 Jan 2015): 7,563,513 specialist outpatient appointments, 733,580 missed = 9.7%. Average outpatient wait 38 days. Delay in specialist care = 25.1% of 14,254 written complaints (2013). The regional health department announced phone contact to "confirm appointments and reassign freed slots". No cost figure. https://www.redaccionmedica.com/autonomias/comunitat-valenciana/20150130/el-absentismo-de-los-pacientes-en-las-consultas-se-evitara-con-recordatorios-telefonicos/335314_0.amp.html
- **[S2] Costa del Sol health area, 2013–14** (Jabalera Mesa doctoral thesis, Universidad de Málaga, 2015). The old PDF link is dead (404). Current record: https://riuma.uma.es/entities/publication/5e36d04e-e88f-4e25-9cc2-c6a623d0127f
  - Table 46: 400,761 appointments, 55,249 missed (13.79%), cost €3,386,919 (14% of €24.2M total outpatient cost). Per site: 256,377 / 36,355 / 14.18% / €2,475,640; 44,848 / 5,468 / 12.19% / €515,936; 99,536 / 13,426 / 13.49% / €395,342. ≈ €61 per missed appointment (our calculation).
  - Table 26, reasons (n=294 non-attenders): forgot 29.6%, communication failure 16.0%, got better 4.8%, physical incapacity 3.7%, admin error 3.4%, dissatisfaction 2.4%, tests pending 1.0%, other 39.1%.
  - Table 29, case vs control means: age 51.28 vs 55.70 (p<0.001); booking delay 25.24 vs 19.15 days (p=0.048); clinic visits in last year 3.60 vs 4.82 (p<0.001). Sex and distance not significant.
  - Literature review (secondary): phone reminders 20→8% (Sawyer 2002), 26→19% (Hashim 2001), −5 points in elderly (Dockery 2001); SMS as effective as calls (Liew 2009) and 15–35% cheaper (Leong 2006, Chen 2008). The thesis concludes SMS is the most cost-effective measure against forgetting.
  - **Correction:** the earlier notes said "wait > 3 months 15.4% vs 8.9%" and "ages 18–35 19.5% vs 10.9% for 65+". Neither is in the thesis. 15.4% is the share of homemakers in the sample; 19.5% is a cell in the sex × group table and a figure cited from a Chinese study. Removed.
- **[S2b]** Journal article from the thesis: *An. Sist. Sanit. Navar.* 2015; 38(2):235–245, DOI 10.4321/S1137-66272015000200007 (882 patients: 294 cases, 588 controls).
  - Checked 2026-10-16 (journal full text). Abstract: "A shorter time period before the appointment and older age were significantly associated with fewer absences, as well as the fact of having attended more consultations in the past year." Conclusion: "Young patients who usually do not visit outpatient clinics are at greatest risk of absence from scheduled appointments in our health area." These are associations from a case-control study, not risk estimates.
  - **Removed:** an earlier draft said the mean cost per appointment ranged from €31.77 to €103.50 by site. That range is not in the journal article or the thesis abstract. The cost paper [S2c] couldn't be fetched, so the range is unverified and is no longer used.
- **[S2c]** Cost paper: *Rev. Calid. Asist.* 2017; 32(4):194–199, DOI 10.1016/j.cali.2017.01.004 (same per-site figures; €12.95 mean extra cost of rebooking).
- **[S3] Regional ombudsman resolution, case file 1259/2021** (Castilla y León, 2021). The complaint was about phone access to a **primary-care** health centre: dropped calls, details taken twice, up to 45 minutes to get through. The ombudsman notes the problems were "even greater for elderly people, those living in rural areas or especially vulnerable". It recommends continued close monitoring of phone service. https://procuradordelcomun.org/archivos/resoluciones/1_1620373534.pdf
- **[S5] Galicia, 2024** (press report, 28 Jan 2025, figures from the regional health service): 948,039 missed appointments in total; hospital outpatient 245,535 missed, rate down from 8.58% (2017) to 5.75% (2024); in-person primary care 3.86% (≈702,504). A GP society spokesperson says hospital appointment SMS go to numbers that aren't kept up to date. No denominator given. https://www.telecinco.es/noticias/galicia/20250127/millon-consultas-perdidas-absentismo-pacientes-sanidad-gallega-2024_18_014594530.html
- **[S6] Tertiary hospital in Castilla-La Mancha, 1–5 Aug 2011**: Pereira-Victorio et al., *Med. Gen. Fam.* 2016; 5:83–90, DOI 10.1016/j.mgyf.2016.02.002. 1,885 new specialist appointments, 276 missed = 14.6%. Reasons (n=186 contacted): didn't know 16.1%, duplicate appointment or went on another date 15.6%, had already cancelled 15.1%, forgot 12.9%, got better 12.4%. Study-week cost €41,908; the annual €3.6–3.7M figures are extrapolations. https://www.elsevier.es/es-revista-medicina-general-familia-edicion-digital--231-articulo-absentismo-pacientes-consulta-externa-especializada-S1889543316000372
- Not usable: "absentismo roza el 11%" (Redacción Médica, Aug 2024) refers to **staff** absenteeism (Randstad Research, Q1 2024), not patient no-shows.
- Regional health portals publish waiting lists per hospital and department. Use only aggregate public figures, with no hospital names in the project.
