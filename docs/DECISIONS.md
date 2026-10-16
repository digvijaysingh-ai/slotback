# Decisions

One line per decision: date · decision · why · alternatives rejected. Full context is in `docs/designs/slotback-full-build.md`.

| Date | Decision | Why | Rejected |
|---|---|---|---|
| 2026-10-16 | Lead use case = outbound confirm/cancel + waiting-list backfill, metric = recovered slots | Two-way contact and backfill are what SMS can't do | Inbound booking first (ElevenLabs already publishes that tutorial) |
| 2026-10-16 | Full scope in 7 days ("breadth wins"), Backfill Ledger at the centre | User's call; the ledger is the differentiator | Minimum cut; depth-only build |
| 2026-10-16 | Slots are freed only by a cancellation or by staff, never by a predicted no-show | Acting on a prediction = AI deciding access to care (AI Act Annex III) | Predictive release |
| 2026-10-16 | Billable slot = filled by the agent AND attended AND matched to the hospital's booking, minus the SMS-arm baseline | A vendor-signed ledger alone is circular | Bill per fill from our own ledger |
| 2026-10-16 | Fictional hospital profile 380k appointments / 12% / 3 sites / 5 specialties | Copying the reference area's exact volumes made it identifiable | 400,761 from [S2] |
| 2026-10-16 | Postgres everywhere, tests included; no SQLite | Concurrency tests must prove production behaviour | SQLite for tests |
| 2026-10-16 | Local tests use `pgserver` (embedded Postgres); CI uses a Postgres service container | Docker isn't installed on the dev machine; no system install needed | Install Docker or Homebrew Postgres |
| 2026-10-16 | Hash chain per hospital per day; every eval run gets its own hospital ID; showcase day read-only | No global lock; evals can't pollute the demo | One global chain; shared data |
| 2026-10-16 | Tools bound to a per-call token; inbound and widget sessions bind on `verify_identity` | A jailbroken agent can't reach other patients | `pid` passed by the LLM |
| 2026-10-16 | Demo calls only to the developer's own phone (allow-list), widget recording is the main demo | Healthcare context; no other number is ever dialled | Twilio trial as the main path |
| 2026-10-16 | Synthetic IDs fail the DNI checksum by construction; phones use non-dialable `+34 000` | Synthetic data must never match a real person | Random valid-looking IDs/phones |
| 2026-10-16 | Generator output pinned by a golden hash (`tests/test_generate.py`) | Demo and evals stay reproducible; changes must be deliberate | Unpinned seed |
| 2026-10-16 | Visual system: warm control room, IBM Plex, ◆ care markers, provenance tag on every number | See DESIGN.md | Inter; blue-black ops UI |
| 2026-10-16 | Evals use ElevenLabs **Tests** (`tests.create` + `agents.run_tests`), not `simulate-conversation` | Simulate endpoint is deprecated and removed 31 Oct 2026; unmocked tools in Tests hit the real webhook | simulate-conversation |
| 2026-10-16 | Per-call token sent as a `secret__` dynamic-variable header; phone calls set it server-side in `conversation_initiation_client_data`; widget sessions are untrusted and bind on `verify_identity` | Widget dynamic variables are set by the browser | Trust widget variables |
| 2026-10-16 | Tool auth = workspace secret in `request_headers` (`secret_id`) | Built-in, never shown to the LLM | Custom auth plumbing |
| 2026-10-16 | Call outcomes: signed `post_call_transcription` + `call_initiation_failure` webhooks (HMAC `ElevenLabs-Signature`); voicemail read from the transcript/termination reason or batch status, plus a timer sweep | Voicemail does not fire `call_initiation_failure` | Tool-only outcomes |
| 2026-10-16 | Postgres embedded in the Space container (pgserver) for the demo; evidence bundles committed under `evidence/` | Co-located (no latency), no third-party DB account; restarts reseed deterministically | Neon/Supabase free tier |
| 2026-10-16 | Production wording: EU data residency and workspace Zero Retention are Enterprise features; ZRM excludes batch calling, so production calls one at a time. The demo claims neither | Docs: "Data residency is an Enterprise feature" | Implying the demo is EU-resident |
| 2026-10-16 | Budget: Starter $6/mo (first month $1), 75 min; extra $0.08/min; text messages $0.003; set the monthly spend cap. Test billing undocumented, so runs are kept small | Pricing page 2026-10-16 | Unbounded nightly suites |
| 2026-10-16 | Showcase dashboard deployed as a static export (free private static Space); live API via the Dockerfile on a Docker host later | HF requires PRO for Docker Spaces | Pay for PRO without asking |
| 2026-10-16 | Doc numbers filled from `metrics/registry.json` through re-fillable markers; anything unmeasured reads "not yet measured" | No invented results; one source for every number | Hand-copied numbers |
| 2026-10-16 | Conversation-level evals report ERRORED until the agent is pushed; the gate is not green | D12: a scenario that didn't run is not a pass | Skipping them |
| 2026-10-16 | Campaign order interleaves specialties by appointment time | A real campaign calls by appointment date | Calling by slot id |
| 2026-10-16 | Live API on Render (free Docker, Frankfurt), approved by the project owner; agents' tools point at it | HF Docker needs PRO | HF PRO |
| 2026-10-16 | Eval finding fixed: upset callers were not offered a person; rule moved to its own early prompt section (`15_upset`) with a scripted line | Rule buried late in the prompt lost to "identity first" | Leaving the gate red |
| 2026-10-16 | Harness bug fixed: tool results arrive as JSON strings; identity detection parses them (regression test) | Substring match gave false leaks on all 3 conversations | Trusting the first FAIL |
| 2026-10-16 | First real phone call (developer's own phone, Twilio trial, synthetic patient): disclosure, identity (one wrong DOB correctly rejected, retry verified) and handoff worked. Two bugs fixed: a confirm call was treated as a backfill offer (`verify_identity` now returns `call_purpose`), and the agent claimed a live transfer and couldn't hang up (`transfer_to_human` returns `callback_requested`; `end_call` added) | Real calls find what text simulations don't | Shipping on simulated evals only |
| 2026-10-16 | Clean demo call after the fixes (2 min, own phone, synthetic patient): disclosure → identity → reads the appointment → offers 3 slots → reads back → moves it → declines a fasting question and promises an admissions callback → hangs up itself. Fixes before it: native Spain-Spanish voice (an English voice reading Spanish sounded like another language), LLM pinned (claude-haiku-4-5), telephone audio format, spare slots in the live day. Fixed after it: the agent promised an email confirmation that doesn't exist | Every real call is reviewed line by line | Calling it done on the happy path |
| 2026-10-16 | Post-call webhook live: HMAC-signed workspace webhook for transcripts and initiation failures; the secret lives only in `.env` and Render env vars | Live call outcomes and transcripts reach the console without polling | Polling the conversations API |
| 2026-10-16 | Published: GitHub repo and showcase Space made public after an audit of the full history (no secrets, no personal data, no real institution as the customer); real call recordings added under `demo/` with annotated transcripts | A deployment is judged on evidence a reader can check | Keeping it private |
