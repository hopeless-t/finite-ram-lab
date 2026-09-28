# CURRENT

> **Latest bounce:** B202
> **Stage:** STRATA-004 / KNEE-REFINEMENT COUNCIL CONVERGED

## Parent result

STRATA-003: 56 / 56 valid trials.

Observed pressure-avoidance bracket:

`32 MiB < knee <= 96 MiB`

## Converged next study

STRATA-004 targeted hosted refinement:

- buffered baseline;
- DONTNEED 32 / 48 / 64 / 72 / 80 / 88 / 96 MiB;
- 8 runner blocks;
- 64 total trials;
- workload shape unchanged from STRATA-003.

Upper-range density is intentional. A simple fit to the 4 / 8 / 16 / 32 MiB pilot points predicts the 160 MiB transition region near ~82 MiB, but this is only a design heuristic, not a result.

## Monte Carlo

Deferred until the empirical transition is localized more tightly.

## Next action

Freeze STRATA-004-KNEE-v1 contract, including runner/kernel/cgroup environment metadata for external-validity tracing.

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default cadence authorized.
