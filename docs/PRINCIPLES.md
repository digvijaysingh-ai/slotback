# Ground rules

These rules applied to every file, commit, call and deploy in this project. The code enforces the ones it can (allow-listed dialling, identity before detail, list order, provenance tags); the rest were checked by hand before publishing.

## Data and naming

- **No real institution is named as the customer.** The customer is fictional: *Hospital General (fictional)*, part of "a regional public health service in Spain". No real hospital's branding is imitated. Real studies are cited only as sources, with their year.
- **Synthetic data only.** No real patient data, ever. Synthetic ID numbers deliberately fail the Spanish DNI checksum; synthetic phone numbers use `+34 000 …`.
- **Real calls go only to the developer's own phone.** The dialler refuses any number outside a one-number allow-list read from the environment.

## Numbers

- **Public figures carry their source and year** and are labelled as benchmarks from other regions (`BENCHMARK [S2, 2013–14]`).
- **No invented results presented as real.** Every Slotback number lives in `metrics/registry.json` with a provenance: `SIMULATED`, `BENCHMARK`, `SYNTHETIC`, `MEASURED` or `ASSUMPTION`. Docs and pages render it with that tag. Anything not yet measured says "not yet measured".

## The agent's limits

- **No clinical advice.** Medical questions are handed to a person.
- **No priority decisions.** The agent offers a freed slot strictly in the order the hospital's list gives; it can't create, score or reorder that list. This keeps it out of the EU AI Act Annex III high-risk area (AI deciding access to public healthcare). The ledger proves the order was followed.
- **AI disclosure first** (AI Act Art. 50), with a recording notice on recorded profiles.
- **Identity before detail:** date of birth plus the last three digits and letter of the ID, checked server-side. Even the specialty is health data.
- **Voicemail or a third party:** a callback number only, never a health detail.
- **A person, or no more automated calls, whenever asked.**

## Legal basis (documented in `docs/05_solution_design.md` and `docs/05b_dpia_draft.md`)

GDPR Art. 6.1.e and 9.2.h; LOPDGDD 3/2018; Ley 41/2002. These are care communications from the hospital to its own patients, not marketing. Vendor side: a GDPR Art. 28 processing agreement, EU data residency and zero retention in production, a DPIA (Art. 35) signed off by the hospital's data protection officer, and ENS (Spain's public-sector security standard).

## Secrets and publishing

- Secrets live in `.env` (gitignored) or the host's environment variables, never in code or history.
- Nothing is published (repo, deploy, post) without the owner's explicit OK.
