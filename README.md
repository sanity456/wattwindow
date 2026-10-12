# WattWindow

Batch B1. A reusable GenLayer intelligent contract for a declared demand response interval. An event owner fixes a context, baseline meter reading, reduction threshold, and distinct operator. The operator submits an actual reading and public report. GenLayer validators independently compare the report with the frozen context and readings. Deterministic arithmetic then records `QUALIFIED`, `NOT_QUALIFIED`, or `UNRESOLVED`.

The report and readings are declarations. A `QUALIFIED` result confirms internal consistency and threshold arithmetic; it does not prove a physical meter or event. Consumers requiring authenticated energy data must add their own trusted meter or attestation process.

## Interface

`open_event(event_key, context, operator, baseline_wh, target_bps)` creates an owner-scoped event. `submit_reading(event_id, actual_wh, report)` is reserved for the designated operator and can run once. `get_event(event_id)` returns canonical JSON; `get_event_count()` returns the number of events.

## Review boundary

The only subjective step is whether the report explicitly supports, contradicts, or leaves uncertain the frozen event and two readings. The validator reruns that classification from the source statements. Reduction is integer basis-point arithmetic outside the nondeterministic block. Inputs are capped, event keys are owner-scoped, roles are distinct, and the event cannot be rewritten after submission.

## Verification

Run `genvm-lint check contracts/watt_window.py`, `genvm-lint typecheck contracts/watt_window.py --strict`, and `pytest -q`. The opt-in `tests/studionet_smoke.py` deploys and exercises the full flow on StudioNet with fresh DPAPI-protected wallets outside this repository. `deployments/studionet.json` records the exact source hash, ABI match, contract address, and finalized transaction hashes. `tests/studionet_release_proof.py` rechecks the deployed source and evidence.

StudioNet deployment: [0x12C9cbBE0f7f4f23147a34B574058ad119908Ca4](https://explorer-studio.genlayer.com/address/0x12C9cbBE0f7f4f23147a34B574058ad119908Ca4). See `AUDIT.md` for the review boundary and test results.
