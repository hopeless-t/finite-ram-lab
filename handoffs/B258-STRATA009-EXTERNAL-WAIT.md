# Bounce Handoff

> **Bounce ID:** B258
> **Status:** EXTERNAL_WAIT / STRATA-009 HOSTED RUN IN PROGRESS

Exact launch commit:

`01e73be662613d164f62287f126ef002c8ff234c`

STRATA-009 run:

`36440093666`

Single status read in B258:

`in_progress`

No second read was performed.

Frozen study:
- cold file 384 MiB
- MemoryMax 320 MiB
- MemoryHigh 160 MiB
- hot anon 64 MiB
- DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 20 trials
- Recorder 98 records/trial
- buffered omitted

Next fresh bounce: read run `36440093666` exactly once.

Success -> fetch aggregate once, validate all 20 trials, compare against 192 MiB anchor, and run pseudo-Council.
Pending -> EXTERNAL_WAIT.
Failure -> inspect only the exposed invariant.

Hosted research only. No local-PC execution. No memory-control policy.
