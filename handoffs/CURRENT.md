# CURRENT

> **Latest bounce:** B254
> **Stage:** STRATA-009 DATASET > MEMORYMAX DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## Parent result

STRATA-008 run `36437651740`: PASS, 24/24.

Cold capacity doubled 96 -> 192 MiB with unchanged:

`80 < K <= 88 MiB`

and bounded sub-MiB non-hot-floor movement.

## STRATA-009

Question:

Can bounded DONTNEED streaming process a one-shot dataset larger than MemoryMax while preserving the same instantaneous-memory response?

Frozen:

- runner Ubuntu 26.04
- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 384 MiB
- read chunk 4 MiB
- DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- no buffered arm in v1
- 4 blocks
- 20 trials
- Recorder 98 records/trial

384 MiB is 1.2x MemoryMax and 2.4x MemoryHigh.

Buffered is omitted to keep the study about bounded-policy science rather than OOM-receipt robustness.

Design:

`docs/STRATA-009-DATASET-GT-MEMORYMAX-v1.md`

## Next fresh-bounce action

Implement:

- spec
- schedule/trial/aggregate
- Ubuntu 26.04 workflow
- tests

Do not launch during implementation.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
Proposal != Decision.
Expressibility != Executability.
