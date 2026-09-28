# CURRENT

> **Latest bounce:** B268
> **Stage:** REC-004 IMPLEMENTED + CI MATERIALIZATION WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Accepted scientific state

Capacity-series knee remains:

`80 < K <= 88 MiB`

for cold capacities 96 / 192 / 384 MiB, including 384 MiB > MemoryMax 320 MiB.

REC-003 identified target-size-dependent residency-observer contamination. Fine historical post-scan floor growth is retired as a workload-law candidate.

## REC-004 implementation

Exact commit:

`d21f0b4ca9b86ab4bc1e2b03d72e4e827198f52d`

Measurement hygiene:

- cold residency verification outside measured cgroup;
- no pre-scan mincore inside measured unit;
- DONTNEED 64 MiB scan;
- capture `post_scan_pre_observer`;
- run historical `_file_residency()`;
- capture `post_scan_post_observer`.

Matrix:
- 96 / 192 / 384 MiB
- 4 blocks
- 12 paired trials
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB

No launch marker exists.

## CI discovery

One exact-head discovery read returned:

`0 matching workflow runs`

Do not infer failure and do not launch yet.

## Next fresh-bounce action

Search exact head `d21f0b4ca9b86ab4bc1e2b03d72e4e827198f52d` for ordinary CI once.

- success -> explicit REC-004 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant;
- absent -> EXTERNAL_WAIT without retry.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
