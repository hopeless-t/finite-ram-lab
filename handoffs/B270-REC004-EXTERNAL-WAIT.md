# Bounce Handoff

> **Bounce ID:** B270
> **Status:** EXTERNAL_WAIT / REC-004 HOSTED RUN IN PROGRESS

Exact launch commit:

`fc0a3d0b8d221777225d7a4a4ae1e5841a0e2367`

Scientific run:

`36443845901`

Single status read in B270:

`in_progress`

No second read was performed.

REC-004 frozen execution:
- 96 / 192 / 384 MiB
- DONTNEED 64 MiB
- hot anon 64 MiB
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- 4 blocks
- 12 paired trials
- pre-observer floor
- historical residency observer
- post-observer floor

Next fresh bounce: read run `36443845901` exactly once.

Success -> fetch aggregate once, validate 12 trials, compare clean vs contaminated floor spans, and decide the prospective measurement contract.
Pending -> EXTERNAL_WAIT.
Failure -> inspect only the exposed invariant.

Hosted research only. No local-PC execution. No memory-control policy.
