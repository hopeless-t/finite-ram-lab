# CURRENT

> **Latest bounce:** B272
> **Stage:** EVIDENCE-001 SQL CORPUS DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## Accepted scientific state

The robust accepted relation remains:

`instantaneous RAM demand ~= effective live set + unreleased streaming interval + bounded overhead`

for the tested one-shot Linux streaming workload.

Capacity series 96 / 192 / 384 MiB shares:

`80 < K <= 88 MiB`

including 384 MiB > MemoryMax.

REC-004 adopts `post_scan_pre_observer` as the prospective clean workload-floor measurement.

## EVIDENCE-001 frozen design

Build a deterministic SQLite corpus over canonical accepted results:

- STRATA-004..009
- REC-003..004

Core tables:
- experiments
- response_cells
- onset_intervals
- measurement_notes

Measurement semantics are explicit:
- clean_pre_observer
- legacy_post_observer
- post_observer_diagnostic
- not_applicable

Required SQL analyses:
- fixed-knee contradiction across pressure
- K+hot interval compatibility
- cold-capacity knee invariance
- clean-floor span
- observer contamination
- next-axis ranking

Design:

`docs/EVIDENCE-001-SQL-CORPUS-v1.md`

## Next fresh-bounce action

Implement:
- schema.sql
- normalized seed JSON
- deterministic SQLite builder
- discovery query bundle
- tests
- hosted workflow gated by launch/EVIDENCE-001-v1.txt

Do not launch during implementation.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
