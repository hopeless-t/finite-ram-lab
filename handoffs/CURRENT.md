# CURRENT

> **Latest bounce:** B206
> **Stage:** STRATA-005 / EXTERNAL-VALIDITY DESIGN FROZEN

## Parent result

STRATA-004: 64 / 64 valid trials.

Hosted anchor at MemoryHigh=160 MiB:

`80 MiB < knee <= 88 MiB`

80 MiB peaked at ~157.86 MiB, so zero median high events does not make it a portable safe default.

## Frozen next study

See `docs/STRATA-005-EXTERNAL-VALIDITY-v1.md`.

Vary one axis first:

- MemoryHigh 144 MiB
- MemoryHigh 176 MiB
- existing 160 MiB result retained as anchor
- arms: buffered, DONTNEED 48 / 64 / 80 / 96 MiB
- 4 runner blocks per new pressure setting
- 40 new hosted trials

Purpose: test whether pressure-event onset is better explained by pressure headroom / normalized coordinates than by one fixed MiB cadence.

## Next action

Implement the frozen STRATA-005 spec/workflow and validation tests **without launching**. Launch is a separate action.

## Monte Carlo

Deferred until cross-pressure empirical observations exist.

## Authority boundary

Hosted research only.
No local-PC execution.
No launch inferred.
No retry/rerun inferred.
No OSS default cadence authorized.
