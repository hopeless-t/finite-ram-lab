# Bounce Handoff

> **Bounce ID:** B107
> **Status:** COMPLETE / GATE POLICY COUNCIL CONVERGED

## Decision

Before a new intervention experiment, derive the selective ACT/NO-ACT policy boundary directly from EXP-003.

Gate inputs:

- initial fault/touch order;
- predicted future HOT identity.

Gate action:

- predicted mismatch -> frozen 16 MiB PAGEOUT of predicted COLD;
- predicted aligned -> NO_HINT fallback.

Stale signal maps exactly to:

- aligned + wrong prediction -> WRONG_PAGEOUT;
- misaligned + wrong prediction -> NO_HINT.

## Frozen analysis

Policy surface over:

- q = 0.10 / 0.25 / 0.50 / 0.75 / 0.90;
- accuracy a = 0.50 ... 1.00.

Report arithmetic total-work and log/geometric total-work separately.

Use 100,000 runner-cluster bootstrap resamples.

## Next action

Snapshot the minimum EXP-003 trial-level policy primitives with provenance.

## Authority boundary

No new GATE-001 experiment is authorized yet.
