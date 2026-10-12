# WattWindow

Batch B1. A reusable GenLayer intelligent contract for a declared demand-response interval. An owner freezes the context, baseline, threshold, operator, and separate witness. The witness first commits a salted hash of a private reading and report, before the operator submits. The witness later reveals the committed reading and report. GenLayer validators independently reconcile the two wallet-bound reports. Only an aligned pair can qualify; numeric disagreement is `DISPUTED`, and incomplete reports are `UNRESOLVED`.

Reports and readings are declarations by distinct wallets. A `QUALIFIED` result confirms attestor agreement and threshold arithmetic; it does not prove a physical meter or event. The owner must appoint a genuinely independent witness for real use.

## Interface

`open_event(event_key, context, operator, witness, baseline_wh, target_bps)` creates an owner-scoped event. The witness calls `commit_witness(event_id, commitment)` with SHA-256 of canonical JSON containing event ID, reading, report, and a 32-character random lowercase hex salt. Only then may the operator call `submit_reading(event_id, actual_wh, report)`. The witness settles once with `witness_reading(event_id, actual_wh, report, salt)`. `get_event(event_id)` returns canonical JSON; `get_event_count()` returns the number of events.

## Review boundary

The subjective step reconciles the two wallet-bound reports with the frozen event and readings. The validator reruns the whole decision, including the substantive assessment. The witness's salted commitment binds its statement before the operator reveals; the reveal is checked deterministically. Numeric disagreement is rejected without AI. Reduction uses integer basis-point arithmetic outside the nondeterministic block. Inputs are capped, keys are owner-scoped, roles are distinct, and settlement is one-time.

## Verification

Run `genvm-lint check contracts/watt_window.py`, `genvm-lint typecheck contracts/watt_window.py --strict`, and `pytest -q`. The opt-in `tests/studionet_smoke.py` deploys and exercises the full flow on StudioNet with fresh DPAPI-protected wallets outside this repository. `deployments/studionet.json` records the exact source hash, ABI match, contract address, and finalized transaction hashes. `tests/studionet_release_proof.py` rechecks the deployed source and evidence.

Current StudioNet deployment: [0x077Ae1775F23F2E05Dc64a57d0Ca77C13e1083fa](https://explorer-studio.genlayer.com/address/0x077Ae1775F23F2E05Dc64a57d0Ca77C13e1083fa). The exact source hash and five finalized transaction receipts are in `deployments/studionet.json`. Do not submit an earlier address. See `AUDIT.md` for the review boundary and test results.
