# CURRENT

> **Latest bounce:** B271
> **Stage:** REC-004 PASS / MEASUREMENT HYGIENE ADOPTED
> **Turn stop reason:** READY_FOR_EVIDENCE_CORPUS_DESIGN

## Accepted finite-RAM result

Across 96 / 192 / 384 MiB cold capacities:

`80 < K <= 88 MiB`

including 384 MiB > MemoryMax 320 MiB.

Leading empirical model:

`instantaneous RAM demand ~= effective live set + unreleased streaming interval + bounded overhead`

for the tested one-shot streaming workload.

## REC-004

Run `36443845901`: PASS, 12/12.

Prospective workload floor is now:

`post_scan_pre_observer`

Historical post-observer floor values remain immutable but are not clean workload-floor measurements.

Clean pre-observer medians:
- 96 MiB: 12.6875 MiB
- 192 MiB: 12.8046875 MiB
- 384 MiB: 12.935546875 MiB

The block-level pattern is not monotonic, so no smooth capacity scaling law is accepted.

Canonical result:

`docs/REC-004-RESULT.md`

## Next fresh-bounce action

Freeze a SQL/queryable evidence-corpus design that normalizes accepted STRATA/REC experiments into a single row-oriented schema.

Minimum dimensions:
- experiment
- run
- block/trial
- runner/image
- MemoryHigh/MemoryMax
- hot anon
- cold capacity
- release cadence
- scan peak
- MemoryHigh events
- OOM
- clean floor when available
- legacy/post-observer floor
- observer delta
- evidence status/provenance

Queries should discover candidate relations and counterexamples without changing raw evidence.

Do not launch physical experiments in the corpus-design bounce.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
