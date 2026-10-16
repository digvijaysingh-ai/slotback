# Design System — Slotback

## Product Context
- **What this is:** the operations dashboard and demo site for an outbound voice agent that confirms specialist appointments and refills freed slots from the waiting list, in the hospital's own order. It also covers the landing page and the readout slides.
- **Who it's for:** a public-hospital director and admissions team (fictional *Hospital General*), and anyone reviewing how the deployment was built.
- **Space/industry:** public healthcare operations, contact-centre tooling, AI voice agents.
- **Project type:** data-dense web app (7 app pages) + one landing page + printed/projected slides.
- **Memorable thing (decision guide, never UI copy):** *Built for patients, careful by design.*

## Aesthetic Direction
- **Direction:** Industrial/utilitarian with a human voice. A warm control room for patient work.
- **Decoration level:** minimal. Type, rules (1 px lines) and numbers do the work. No illustrations, gradients, shadows or decorative icons.
- **Mood:** calm, precise and humane. Serious enough for a hospital director, readable at a glance by an admissions clerk.
- **Signature elements:**
  1. **Warm charcoal**, not blue-black. It reads human, not "NOC wallboard".
  2. **Care markers (◆).** AI disclosed, identity verified, read back, handed to a human. The same outlined sage marker appears wherever a safeguard happens: transcripts, ledger, call board, readout.
  3. **Numbers are the only hero.** Key metrics are set large in Plex Mono with a provenance tag underneath. Charts appear only when they answer a question.
- **Reference (principles only, never imitate branding):** public-service design systems for plain language and colour-independent meaning (NHS service manual, GOV.UK Frontend, Aragón DESY); contact-centre wallboards for the density of the call board.
- **Approved visuals:**
  - [`docs/img/design/impact-mockup-variant-b.png`](docs/img/design/impact-mockup-variant-b.png) (layout direction, approved mock-up)
  - [`docs/img/design/design-system-preview.html`](docs/img/design/design-system-preview.html) (system preview, with dark/light toggle; open locally)

## Typography
- **Display/Hero numbers:** IBM Plex Mono 600, `font-variant-numeric: tabular-nums`. Numbers line up and look measured.
- **Headings:** IBM Plex Sans 600. Institutional, highly legible, made for enterprise software.
- **Body/UI/Labels:** IBM Plex Sans 400/500.
- **Data/Tables/Ledger/IDs/hashes/tags:** IBM Plex Mono 400/500, tabular.
- **Code:** IBM Plex Mono.
- **Loading:** Google Fonts, `IBM+Plex+Sans:wght@400;500;600` and `IBM+Plex+Mono:wght@400;500;600`, `display=swap`. Self-host from `static/fonts/` for the Space if needed (OFL licence).
- **Never:** Inter, Roboto, Arial, system-ui as the primary face.
- **Scale (px):**

  | Size | Use |
  |---|---|
  | 12 | tags, captions |
  | 14 | table cells, ledger |
  | **16** | body, minimum for running text |
  | 20 | lede |
  | 24 | section |
  | 32 | page title, secondary metric |
  | 48 | landing headline |
  | 72 | hero metric |

  Line-height is 1.5 for body and 1.1–1.2 for display.
- **Copy rules:**
  - Use patient-centred labels: "Patients reached", "Slots returned to the waiting list". Never "calls dialled" or "handle time".
  - Use utility language for orientation, status and action.
  - Spanish and English both exist (EN is the default on the public demo; Spanish is used in calls, transcripts and `readout/es`).

## Color
- **Approach:** restrained. One accent; every other colour carries a meaning.
- **Status always uses colour + icon + label**, never colour alone. The icons are: ✓ filled/ok, ⟳ offering, ✕ unfilled/error, ◆ care marker.

| Token | Dark (app, default) | Light (print / projector) | Use |
|---|---|---|---|
| `--bg` | `#151412` | `#FBFAF7` | page |
| `--surface` | `#1C1A17` | `#FFFFFF` | rails, panels, table bodies |
| `--raised` | `#24221E` | `#F3F1EC` | selected nav, chips |
| `--line` | `#34312B` | `#DEDAD1` | 1 px rules, borders |
| `--text` | `#ECE8E1` | `#1B1A17` | primary text |
| `--muted` | `#A39D92` | `#5E5A52` | labels, secondary text |
| `--accent` (clinic blue) | `#7AB3EA` | `#1F5FA8` | primary action, links, focus ring, current nav |
| `--accent-ink` | `#0E1B28` | `#FFFFFF` | text on accent |
| `--ok` | `#86C98F` | `#2E7D3E` | ✓ filled, verified |
| `--offering` | `#E8B860` | `#8A5A00` | ⟳ offering, warnings |
| `--unfilled` | `#EF8A80` | `#B3261E` | ✕ unfilled, errors, destructive actions |
| `--care` | `#9FD3C7` | `#1F6F60` | ◆ care markers (outline style, never filled) |
| `--sim-fg` / `--sim-bg` | `#F2C14E` / `#3A2C0E` | `#6B4A00` / `#FFE7A8` | SIMULATED badge (filled) |
| `--bench` | `#9DB4CC` | `#3D5A78` | BENCHMARK [source, year] tag (outline) |
| `--synth` | `#A39D92` | `#5E5A52` | SYNTHETIC tag (outline) |
| `--meas` | `#86C98F` | `#2E7D3E` | MEASURED tag (outline) |

- **Contrast (checked 2026-10-16):** every text pairing ≥ 4.5:1. Muted on bg is 6.8, accent on bg 8.3, care on surface 10.4, SIMULATED badge 8.1, light muted 6.6, light offering 5.9, light ok 5.1. Re-check any new pairing.
- **Dark/light strategy:**
  - Dark is the app.
  - Light is for printed and projected readout slides, and an optional user toggle.
  - Semantics are identical in both; light values are darkened for AA on white.
- **Provenance tags (D28):** every number carries exactly one tag: `SIMULATED` · `BENCHMARK [S#, year]` · `SYNTHETIC` · `MEASURED`. Values come from `metrics/registry.json`.

## Spacing
- **Base unit:** 4 px.
- **Density:** comfortable-compact.
- **Scale:** 2xs(2) xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48) 3xl(64).
- **Tables:** cell padding 10 px × 12 px, row height ≥ 44 px (touch target).
- **Sections:** 24 px inside panels, 32–56 px between page sections.

## Layout
- **Approach:** grid-disciplined. The app has three regions: **left rail** (180–200 px), **workspace**, **context panel** (300–330 px: ledger, details).
- **Grid:** 12 columns, 24 px gutters. Max content width 1600 px (app) and 1280 px (landing, docs).
- **Breakpoints:**
  - ≥1024 full layout.
  - 768–1023: the context panel moves below the workspace; the rail becomes icons with labels on focus or hover.
  - <768: **read-only summary** (headline number, replay as a vertical event list, verify status, link to the video). No actions on phones.
- **Border radius:** sm 2 px (tags, markers), md 4 px (buttons, panels, inputs). Never pill shapes, never large rounding.
- **Cards:** only where the card *is* the interaction. Metrics sit on the page with rules between them, not in boxes. The landing page is one composition, not a grid of boxes.
- **Every page** carries a context bar: "Fictional hospital · synthetic data · simulated results are labelled".

## Motion
- **Approach:** minimal-functional. State changes only.
- **Easing:** enter `ease-out`, exit `ease-in`, move `ease-in-out`.
- **Duration:** micro 80 ms, short 150–250 ms, medium 300 ms. Nothing longer except the replay.
- **The only choreography:** the 60-second Impact replay (markers step freed → offering r1/r2 → filled, the counter climbs, ledger lines appear in sync). It can be paused and scrubbed. With `prefers-reduced-motion`, it steps through states without animating.
- **No** autoplay, parallax, entrance animations or animated backgrounds.

## Components (vocabulary)
- **Buttons:** primary (accent fill) · secondary (1 px line) · danger (unfilled outline, e.g. "Tamper with one event") · ghost (accent text). Minimum height 44 px. Visible 2 px accent focus ring.
- **Alerts:** a 3 px left rule in the semantic colour on a surface background, with a bold first sentence that says what happened and a link to the next action.
- **Status chip:** icon + label in its semantic colour, no fill.
- **Care marker:** `◆ label`, 1 px outline in `--care`, 2 px radius, 13 px Plex Sans 500.
- **Provenance tag:** 11 px Plex Mono, uppercase. SIMULATED is filled; the rest are outlined.
- **Ledger row:** `#seq` (muted mono) + event (mono). Care events are prefixed ◆ in `--care`; the final state is ✓ in `--ok`.
- **Tables:** left-aligned text; right-aligned tabular numbers; 1 px row rules; no zebra stripes.

## Accessibility
- WCAG 2.2 AA minimum (see contrast). Body text ≥ 16 px.
- Meaning never carried by colour alone.
- Full keyboard operation: nav, replay play/pause/scrub, tamper/restore, verify upload, all actions.
- ARIA landmarks (`nav`, `main`, `complementary`). The live counter is announced with `aria-live="polite"`, throttled to once every 5 s.
- `prefers-reduced-motion` respected. Touch targets ≥ 44 px.
- Specialty and any appointment detail stay hidden in the UI until identity is verified (shown as "—").

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-10-16 | Initial design system created | /design-consultation from approved direction B ("Control room") + research on public-health and contact-centre UIs |
| 2026-10-16 | IBM Plex Sans + Plex Mono, Inter dropped | Institutional and legible, with tabular figures; Inter reads as a template |
| 2026-10-16 | Warm charcoal dark instead of blue-black | Memorable thing is "careful, for patients"; cold ops palettes read as throughput tools |
| 2026-10-16 | ◆ care-marker language | Makes safeguards (AI disclosure, identity, read-back, human handoff) visible everywhere |
| 2026-10-16 | Numbers as the only hero; provenance tag on every number | Credibility over decoration; the "no invented results" rule made visible |
| 2026-10-16 | Light token set for slides | Dark slides wash out on projectors and in print |
| 2026-10-16 | Remaining defaults set during design, approved in bulk | Exact hex values, type scale, 4 px spacing, 2/4 px radius, motion durations |
