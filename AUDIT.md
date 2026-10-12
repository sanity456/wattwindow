# Release audit

- Mechanism (v2): frozen baseline and threshold, a distinct operator's reading, a separate witness's reading, validator-reviewed reconciliation of both wallet-bound reports, and deterministic basis-point qualification. Numeric disagreement is disputed before any LLM call.
- Source policy: the model sees only public caller-supplied text and integers. There is no scrape, private API, or claim that a meter is authenticated.
- Security: owner-scoped keys, three distinct nonzero roles, one-time submissions, numeric/text limits, immutable final state, strict result parsing, and an independent validator rerun before updating state. No tokens or funds are held.
- Local gates: GenVM lint and strict type check passed; 3 v2 direct tests passed, including role authorization, conflicting readings, malformed output, and validator disagreement.
- StudioNet gate: fresh v2 deployment, open/operator/witness flow, and read-only release proof passed with three isolated wallets. The deployed source is byte-identical to `contracts/watt_window.py`, the ABI matches, and all four receipts finalized. The v1 address must not be submitted as evidence for this source.
- Limits: distinct wallet attestations and consensus reconciliation establish accountable agreement, not physical proof of demand response. Witnesses can collude or copy; a real deployment needs an independent witness-selection policy.
