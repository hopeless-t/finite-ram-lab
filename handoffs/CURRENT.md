# CURRENT

> **Latest bounce:** B341
> **Stage:** MEMCG-005D RUNTIME REPAIR / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## MEMCG-005C

Canonical:
`909b554048e4e269ebb644c8533857468cae8296`

Decision:
`REJECT_ATOMIC_PATH`

## MEMCG-005D

Implementation:
`bac7f0babe87a7350f81ea37113b3798b512ca7d`

Initial scientific launch:
`f4ca08442547142f1aaf0d0113f0653da3d7ee09`

Failed run:
`36552551097`

Failure:
unaligned `mmap.flush(offset,4)` in Python latch helper caused `EINVAL`.

Repair:
`c89fec2940537f610ee517885c1d9e813d79f3c6`

Scientific design unchanged:
- SELF_ATOMIC worker self-migration;
- EXTERNAL_ATOMIC controller-driven migration;
- external pre/mid/post current decomposition;
- shared latch, no measured-path status I/O.

No new scientific launch marker has been created after the repair.

## Next fresh-bounce action

Discover/read ordinary CI for repair commit exactly once.

- success -> create a new explicit MEMCG-005D repair launch marker/path or otherwise explicit new launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
