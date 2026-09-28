# CURRENT

> **Latest bounce:** B203
> **Stage:** STRATA-004 / KNEE REFINEMENT FROZEN

## Parent result

STRATA-003: 56 / 56 valid trials.

Observed pressure-avoidance bracket:

`32 MiB < knee <= 96 MiB`

## Frozen STRATA-004 contract

See:

- `docs/STRATA-004-KNEE-v1.md`
- `specs/STRATA-004-KNEE-v1.json`

Arms:

- buffered
- DONTNEED 32 / 48 / 64 / 72 / 80 / 88 / 96 MiB

Design:

- 8 runner blocks
- 64 total trials
- workload shape unchanged from STRATA-003
- runner/kernel/cgroup provenance captured for later external-validity work

## Monte Carlo

Deferred until empirical transition localization is tighter.

## Next action

Implement the frozen hosted study without changing the historical STRATA-003 contract.

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default cadence authorized.
