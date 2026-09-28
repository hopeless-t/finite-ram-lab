# Bounce Handoff

> **Bounce ID:** B205
> **Status:** COMPLETE / STRATA-004 PASS CANONICALIZED

## Result

STRATA-004 run `36392457515` completed successfully.

64 / 64 trials valid.

Observed median MemoryHigh events:

- 32 / 48 / 64 / 72 / 80 MiB: 0
- 88 MiB: 2
- 96 MiB: 5
- buffered: 5

Hosted pressure-avoidance knee bracket is refined to:

`80 MiB < knee <= 88 MiB`

## Interpretation

80 MiB is not an OSS default candidate merely because it avoided median pressure events. Its median peak scan memory (~157.86 MiB) sits close to the 160 MiB MemoryHigh boundary.

Timing is noisy and non-monotonic; no throughput default is selected.

## Council

Converged on external-validity work next. Do not spend the next experiment merely interpolating 80–88 MiB on the same substrate.

## Monte Carlo

Deferred until cross-substrate or cross-pressure empirical distributions exist.

## Next action

Design a hosted external-validity study that varies pressure headroom and/or runner substrate while preserving the workload and evidence contract.

## Authority boundary

Hosted research only. No local-PC execution. No OSS default cadence authorized.
