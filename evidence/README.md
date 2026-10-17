# Evidence: verify the ledger yourself

A hospital can't pay per recovered slot unless it can check the work. Every step Slotback takes (disclosure, identity check, offer, accept, decline, fill) is an event in a per-hospital, per-day **hash chain**, and each day's head is **signed** (Ed25519). This folder holds the signed bundle for the synthetic showcase day, so anyone can check it without trusting the dashboard.

| File | What it is |
|---|---|
| `showcase-2026-10-16.zip` | The bundle: `ledger.jsonl` (1,707 events), `list_snapshots.jsonl` (the waiting-list order at the moment each slot was freed, pseudonymous IDs only) and `head.json` (the signed chain head) |
| `trusted_key.txt` | The public key the head must be signed with. In production the hospital keeps this, not the vendor. |

## Run it

```bash
uv sync
uv run voiceledger verify evidence/showcase-2026-10-16.zip --trusted-key $(cat evidence/trusted_key.txt) --rules voiceops.toml
```

```
PASS  1707 events
  PASS         chain: 1707 events linked
  PASS         identity_before_detail: 300 detail_disclosed events, all after identity_verified
  PASS         list_order: 14 snapshots followed in order (per slot_id)
  PASS         head: signed head matches
```

Or upload the zip on the dashboard's **Verify** page.

## What each check proves

| Check | Proves |
|---|---|
| `chain` | No event was edited, inserted or deleted after it was recorded. Each hash covers the event and the previous hash. |
| `identity_before_detail` | No appointment detail was disclosed on a call before that call's identity check passed. |
| `list_order` | Every freed slot was offered rank 1, then 2, then 3… in the hospital's own list order, as snapshotted when the slot was freed. The agent never chose who got a slot. |
| `head` | The final hash matches a head signed with the trusted key, so the whole day can't be regenerated and re-signed by someone without that key. |

## Try to break it

Change one patient ID in event #11 (an accepted offer) and verify again:

```
FAIL  1707 events
  FAIL         chain at #11: event was changed after it was recorded
  PASS         identity_before_detail: 300 detail_disclosed events, all after identity_verified
  FAIL         list_order at #11: pid at rank 1 does not match the snapshot
  PASS         head: signed head matches
```

The dashboard's **Impact** page has a "Tamper with one event" button that does the same live.

## What it does not prove

The ledger is evidence, not the bill. It shows the record wasn't rewritten after the hospital received the signed head; it doesn't prove a call happened the way it says. That's why billing counts only fills that also match the hospital's own booking record and were attended, minus the share staff would have refilled anyway (`docs/04_business_case.md`, §6).

The showcase day is **synthetic and simulated**: 400 appointments, generated patients, assumed behaviour (`slotback/sim/day.py`). The ledger and verifier code are the same as in the live API.
