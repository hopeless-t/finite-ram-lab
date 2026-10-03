# FR-GFX-007 — Causal Sidecar Join Receipt

Status: **PASS / CAUSAL LATEST-KNOWN JOIN VALIDATED**

## Qualification

- workflow run: 37109447241
- job: 111164357180
- execution head: e1aa02997891b0947c25c9a09eb7d343b2a017fc
- targeted tests: 5/5 PASS
- artifact ID: 11268684519
- artifact ZIP SHA256: faebe5bc68c03029d8e7798b788308dc4325a1f02917077a17420cf226b41ed4
- spec SHA256: 8c8b68b7efadc387c293f273baa68a6a439c3848bae5adb9d21ba6064aa9ee52
- result SHA256: 18baef41dc5bd97db5a07d3ac2a783c51d429090439c3dc625a499040f6d3548

## Frozen invariants

- latest-known-only join;
- future leakage count: 0;
- stale evidence is explicit;
- missing evidence is explicit;
- stale/missing GPU values are never coerced to zero;
- backend identity is explicit.

## Adversarial fixture

A frame sample exists at t=3100 while the target control record is at t=3000.

The causal join refuses the future sample.

It sees the last past sample at t=1900 and rejects it as stale under the frozen
max-age rule.

## Claim ceiling

**CAUSAL_OFFLINE_JOIN_CONTRACT_ONLY**
