# CURRENT

> **Latest bounce:** B205
> **Stage:** STRATA-004 / PASS CANONICALIZED

## Result

STRATA-004: 64 / 64 valid trials.

Hosted pressure-event response:

- DONTNEED 32 / 48 / 64 / 72 / 80 MiB: median MemoryHigh events = 0
- 88 MiB: 2
- 96 MiB: 5
- buffered: 5

Current hosted knee bracket:

`80 MiB < knee <= 88 MiB`

See `docs/STRATA-004-KNEE-RESULT.md`.

## Important boundary observation

80 MiB peaks at ~157.86 MiB against MemoryHigh=160 MiB. Zero median high events does not make it a portable safe default.

Hosted throughput is noisy/non-monotonic and is not a selection signal.

## Next action

Explore and converge a small external-validity study. Prefer testing whether cadence should scale with pressure headroom instead of freezing a single MiB constant.

## Monte Carlo

Deferred until empirical cross-pressure or cross-substrate distributions exist.

## Authority boundary

Hosted research only.
No local-PC execution.
No retry/rerun inferred.
No OSS default cadence authorized.
