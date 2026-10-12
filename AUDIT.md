# Release audit

- Mechanism (v3): frozen baseline and threshold, a witness's salted reading/report commitment before the operator's submission, a verified witness reveal, validator-reviewed reconciliation of both wallet-bound reports, and deterministic basis-point qualification. Numeric disagreement is disputed before any LLM call.
- Source policy: the model sees only public caller-supplied text and integers. There is no scrape, private API, or claim that a meter is authenticated.
- Security: owner-scoped keys, three distinct nonzero roles, a 128-bit salted witness commitment that prevents copying after operator publication, one-time submissions, numeric/text limits, immutable final state, strict result parsing, and an independent validator rerun before updating state. No tokens or funds are held.
- Local gates: v3 GenVM lint and strict type check passed; three direct tests passed, including unauthorized order, wrong-salt reveal, numeric disagreement, malformed model output, and validator disagreement.
- StudioNet gate: fresh v3 deployment, open/commit/operator/reveal flow, and read-only release proof passed with three newly isolated wallets. Deployed source bytes and ABI match this repository; all five receipts finalized. The v1 and v2 addresses must not be submitted as evidence for this source.
- Limits: distinct wallet attestations and consensus reconciliation establish accountable agreement, not physical proof of demand response. The witness can still collude before commitment; a real deployment needs an independent witness-selection policy.
