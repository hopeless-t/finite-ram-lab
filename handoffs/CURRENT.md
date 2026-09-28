# CURRENT

> **Latest bounce:** B209
> **Stage:** REC-002 / RECORDER OVERHEAD DESIGN FROZEN

## REC-001

REC-001 v0 implementation commit:

`496b0203c3075b22394aafdfb13ccb438d6331c5`

Hosted CI run `36416819473` completed with conclusion `success`.

The implementation is accepted as repository-valid.

## Frozen next study

See `docs/REC-002-OVERHEAD-v1.md`.

REC-002 tests observer effect in a sensitive hosted boundary condition:

- MemoryHigh = 160 MiB
- MemoryMax = 320 MiB
- hot anonymous memory = 64 MiB
- cold file = 96 MiB
- DONTNEED = 80 MiB
- recorder_off vs recorder_on
- 8 paired runner blocks
- 16 total trials
- recorder_on emits 26 JSONL records per trial
- SQLite ingest stays outside the pressure-sensitive interval

Primary outcomes:

- MemoryHigh event delta;
- maximum scan memory.current;
- scan elapsed time;
- JSONL bytes written.

## Parent research state

STRATA-005 external-validity design remains frozen from B206 and unchanged.

## Next action

Implement REC-002 and its validation tests. Hosted launch remains a separate execution step.

## Authority boundary

Hosted research/repository work only.
No local-PC execution.
No STRATA-005 launch inferred.
No memory-control policy authorized.
