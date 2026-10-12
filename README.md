# WattWindow

Batch B1. A reusable GenLayer intelligent contract for a declared demand-response interval. An owner freezes the context, baseline, threshold, operator, and separate witness. The operator and witness sign distinct on-chain reports. GenLayer validators independently reconcile both reports with the frozen interval and readings. Only an aligned pair can qualify; numeric disagreement is `DISPUTED`, and incomplete reports are `UNRESOLVED`.

Reports and readings are declarations by distinct wallets. A `QUALIFIED` result confirms attestor agreement and threshold arithmetic; it does not prove a physical meter or event. The owner must appoint a genuinely independent witness for real use.

## Interface

`open_event(event_key, context, operator, witness, baseline_wh, target_bps)` creates an owner-scoped event. `submit_reading(event_id, actual_wh, report)` is reserved for the operator. `witness_reading(event_id, actual_wh, report)` is reserved for the witness and settles once. `get_event(event_id)` returns canonical JSON; `get_event_count()` returns the number of events.

## Review boundary

The subjective step reconciles the two wallet-bound reports with the frozen event and readings. The validator reruns the whole decision, including the substantive assessment. Numeric disagreement is rejected without AI. Reduction uses integer basis-point arithmetic outside the nondeterministic block. Inputs are capped, keys are owner-scoped, roles are distinct, and settlement is one-time.

## Verification

Run `genvm-lint check contracts/watt_window.py`, `genvm-lint typecheck contracts/watt_window.py --strict`, and `pytest -q`. The opt-in `tests/studionet_smoke.py` deploys and exercises the full flow on StudioNet with fresh DPAPI-protected wallets outside this repository. `deployments/studionet.json` records the exact source hash, ABI match, contract address, and finalized transaction hashes. `tests/studionet_release_proof.py` rechecks the deployed source and evidence.

Current StudioNet deployment: [0x5991Cd9efA516f5a20B8559BE8ECD4906Dfd6239](https://explorer-studio.genlayer.com/address/0x5991Cd9efA516f5a20B8559BE8ECD4906Dfd6239). The exact source hash and finalized receipts are in `deployments/studionet.json`. Do not submit the older address. See `AUDIT.md` for the review boundary and test results.
