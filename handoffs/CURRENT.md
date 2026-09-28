# CURRENT

> **Latest bounce:** B270
> **Stage:** REC-004 / HOSTED RUN LAUNCHED + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Accepted scientific state

Capacity-series knee remains:

`80 < K <= 88 MiB`

for 96 / 192 / 384 MiB, including 384 MiB > MemoryMax 320 MiB.

REC-003 showed target-size-dependent observer contamination. Historical fine post-scan floor growth is retired as a workload-law candidate.

## REC-004

Exact launch commit:

`fc0a3d0b8d221777225d7a4a4ae1e5841a0e2367`

Scientific run:

`36443845901`

Single B270 read:

`in_progress`

Do not poll again in this bounce.

Frozen execution:
- 96 / 192 / 384 MiB
- DONTNEED 64 MiB
- hot anon 64 MiB
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- 4 blocks
- 12 paired trials

Each trial measures:
1. post_scan_pre_observer
2. historical _file_residency()
3. post_scan_post_observer

Question: does the clean workload floor stay capacity-bounded while the observer introduces the small size-dependent shift?

## Next fresh-bounce action

Read run `36443845901` exactly once.

- success -> fetch aggregate once and validate/atomize 12 trials;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
