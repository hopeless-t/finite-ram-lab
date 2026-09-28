# CURRENT

> **Latest bounce:** B269
> **Stage:** REC-004 / EXPLICIT HOSTED LAUNCH
> **Turn stop reason:** RUN_DISCOVERY_PENDING

Implementation CI `36443368060`: completed / success.

Exact launch commit:

`fc0a3d0b8d221777225d7a4a4ae1e5841a0e2367`

REC-004 frozen execution:
- capacities 96 / 192 / 384 MiB
- DONTNEED 64 MiB
- hot anon 64 MiB
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- 4 blocks
- 12 paired trials

Each trial captures:
1. post_scan_pre_observer
2. historical _file_residency()
3. post_scan_post_observer

Question: does the clean pre-observer floor stay bounded while observer delta reproduces the contamination?

Next fresh-bounce action: discover/read REC-004 for exact launch commit once.

Hosted research only. No local-PC execution. No memory-control policy.
