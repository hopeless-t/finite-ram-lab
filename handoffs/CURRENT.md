# CURRENT

> **Latest bounce:** B207
> **Stage:** REC-001 / RECORDER v0 DESIGN FROZEN

## Parent research state

STRATA-005 external-validity design remains frozen from B206.

It varies MemoryHigh at 144 and 176 MiB, retains 160 MiB as the existing anchor, and keeps the existing workload/runner family. See `docs/STRATA-005-EXTERNAL-VALIDITY-v1.md`.

## Council decision

Before STRATA-005 implementation, add a deliberately small observation-only evidence recorder.

See:

- `docs/REC-001-COUNCIL.md`
- `docs/REC-001-RECORDER-v0.md`

## Frozen recorder contract

- JSONL is canonical raw evidence.
- SQLite is a rebuildable query projection.
- records are schema-versioned;
- measurements, events, and derived summaries remain distinct;
- provenance is explicit;
- duplicate ingestion must be idempotent or fail on conflict;
- v0 performs no reclaim/control action.

## Critical validation

Recorder overhead is itself an experimental concern. Before recorder-instrumented performance claims become authoritative, recorder-on versus recorder-off overhead must be measured.

## Next action

Implement the minimal stdlib REC-001 recorder and SQLite ingester with tests. Do not launch STRATA-005 yet.

## Authority boundary

Hosted research/repository work only.
No local-PC execution.
No STRATA-005 launch inferred.
No memory-control policy authorized.
