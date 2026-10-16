# Call 01 · The first real call (before fixes)

**Audio:** [`01-first-real-call-before-fixes.mp3`](01-first-real-call-before-fixes.mp3) · 3 min 9 s · 16 Oct 2026
**Setup:** same as [call 02](02-confirm-and-reschedule.md): Twilio to the developer's own phone, synthetic patient, live API. At this point the agent had passed all 15 simulated eval scenarios.

**Why it's here:** text simulations passed, and the first real call still found four problems. All four were fixed the same day and logged in [`docs/DECISIONS.md`](../../docs/DECISIONS.md). Call 02 is the same flow after the fixes.

## What went right

- AI disclosure and recording notice first.
- The patient first gave the wrong date of birth ("12 de diciembre" instead of the 2nd). `verify_identity` returned `failed, attempts_left: 1`; the agent asked again, and only the corrected answer verified. Nothing about the appointment was said before that.
- When a tool returned an error, the agent didn't improvise: it offered a person.

## What went wrong, and the fix

| # | What happened | Root cause | Fix |
|---|---|---|---|
| 1 | The voice sounded like it was speaking another language. | The agent used the platform's default **American English voice** to read Spanish. The text transcript was 100% Spanish. | A native Spain-Spanish voice; LLM pinned to `claude-haiku-4-5` instead of a platform default; telephone audio format (μ-law 8 kHz) on the phone agent. |
| 2 | On a confirmation call, the agent said "we have a freed slot and you're next on the waiting list" and called `offer_backfill`. The server refused (`not_eligible: not a backfill call`). | The outbound prompt had no way to know why it was calling. | `verify_identity` now returns `call_purpose`; the backfill steps apply only when it is `backfill`. |
| 3 | After `transfer_to_human`, the agent kept saying "I'm transferring you" while nothing happened, and the patient said "you haven't transferred me". | The demo has no live line to admissions; the tool said `transferring` anyway. | The tool returns `callback_requested`; the agent says admissions will call back. |
| 4 | Goodbyes looped until the patient hung up. | The agent had no way to end a call. | The `end_call` system tool, called after `log_outcome` and one goodbye. |

The server-side guard in row 2 is the design working as intended: the agent can only act through tools, and the tools check what each call is allowed to do. The prompt fix made the agent stop trying.

## Transcript (abridged, Spanish with English)

| Speaker | Spanish | English |
|---|---|---|
| Agent | Hola, le llamo del Hospital General. Soy un asistente de inteligencia artificial y esta llamada se graba… | Hello, calling from Hospital General. I'm an AI assistant and this call is recorded… |
| Patient | 12 de diciembre de 1955. · 453Z. | 12 December 1955. · 453Z. |
| | `verify_identity` → `failed`, 1 attempt left | |
| Agent | Lo siento, los datos no coinciden. ¿Me lo puede repetir una vez más? | Sorry, the details don't match. Could you repeat them once more? |
| Patient | 2 de diciembre de 1955. · 453Z. | 2 December 1955. · 453Z. |
| | `verify_identity` → `verified` | |
| Agent | Llamo porque tenemos una cita liberada y usted es la siguiente persona en la lista de espera. | I'm calling because a slot has been freed and you're next on the waiting list. **(bug 2)** |
| | `offer_backfill` → `not_eligible` | Server refuses: this is not a backfill call |
| Agent | Disculpe, ha habido un problema al consultar la cita. ¿Le paso con una persona de admisión? | Sorry, there was a problem. Shall I pass you to admissions? |
| Patient | Sí. | Yes. |
| | `transfer_to_human` → `transferring` | **(bug 3)** |
| Agent | Le paso con una persona de admisión… Hasta luego. | Transferring you… goodbye. |
| Patient | Pero no me ha pasado con una persona de admisión. | But you haven't transferred me. |
| Agent | Tiene razón, disculpe. Le paso ahora mismo… ¿Sigue ahí? | You're right, sorry. Transferring now… Are you still there? **(bugs 3, 4)** |
