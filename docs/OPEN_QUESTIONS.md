# Open questions

Parked items. Each one names who or what resolves it.

| # | Question | Resolves it | Status |
|---|---|---|---|
| 1 | ElevenLabs platform facts: tool auth headers; trusted dynamic variables for widget vs phone; do simulations call real webhooks; post-call webhook events and signature; batch-calling outcomes; built-in evaluation | Day-1 platform check (docs) | **Answered 2026-10-16** (see DECISIONS) |
| 2 | Starter plan price and minutes; do text simulations consume credits; spend cap | Day-1 platform check | **Partly answered**: Starter $6/mo (first month $1), 75 min; test/simulation billing not documented |
| 3 | EU data residency and zero retention: which plan | Day-1 platform check | **Answered**: residency = Enterprise; demo claims neither |
| 4 | AI Act Art. 50 (AI disclosure): in force since 2 Aug 2026, or delayed? | Check before the readout states it | Open |
| 5 | Free Postgres provider and region (co-located with the HF Space) | Decided: embedded Postgres in the Space | **Closed** |
| 6 | Twilio: account, number, Spain geo permission for the bonus call | User is setting it up; quote cost first | Open |
| 7 | When to create the private GitHub repo and push (CI needs it) | User confirmed 2026-10-16 | **Closed**: private repo created |
| 8 | ElevenLabs API key lacks the Agents permission (convai_read / convai_write): blocks pushing the agent and running ElevenLabs Tests | User: enable the permission on the key | **Closed 2026-10-16**: new key works; inbound and outbound demo agents pushed (tool URL pending hosting) |
| 9 | Hosting for the live API: Hugging Face requires PRO for Docker Spaces. Options: HF PRO, or another Docker host (Render, Fly.io, Koyeb) | Owner decision (cost/account) | **Closed 2026-10-16**: Render free Docker service, https://slotback-api.onrender.com (approved by the project owner) |
| 10 | Making the Space and the GitHub repo public | Owner confirmation | **Closed 2026-10-16**: both public after a secrets and personal-data audit of the full history |
| 11 | Post-call webhook: configure the workspace webhook in ElevenLabs (HMAC secret) so live call transcripts and outcomes reach the console | Done 2026-10-16: HMAC workspace webhook → `/hooks/post-call` for `transcript` and `call_initiation_failure`; secret on Render only; unsigned/bad signatures return 401 on the live API | Closed |
