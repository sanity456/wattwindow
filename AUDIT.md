# Release audit

- Mechanism: frozen baseline and threshold, a distinct operator's declared actual reading, consensus-reviewed report consistency, and deterministic basis-point qualification. No matching multi-reporter or time-series algorithm is used.
- Source policy: the model sees only public caller-supplied text and integers. There is no scrape, private API, or claim that a meter is authenticated.
- Security: owner-scoped keys, one-time operator submission, numeric/text limits, immutable final state, strict result parsing, and an independent validator rerun before updating state. No tokens or funds are held.
- Local gates: GenVM lint and strict type check passed; 3 direct tests passed, including authorization, malformed output, and validator disagreement.
- StudioNet gate: full deploy/open/submit flow passed with 2 fresh isolated wallets; final state `QUALIFIED`; read-only release proof passed. The manifest records finalized receipt hashes and a byte-identical deployed source and matching ABI.
- Limits: a qualifying report is a consistency and arithmetic result on declarations, not physical proof of demand response.
