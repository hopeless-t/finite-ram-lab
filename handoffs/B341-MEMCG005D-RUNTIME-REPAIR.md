# Bounce Handoff

> **Bounce ID:** B341
> **Status:** MEMCG-005D RUNTIME INFRA FAILURE REPAIRED

Scientific launch:
`f4ca08442547142f1aaf0d0113f0653da3d7ee09`

Failed scientific run:
`36552551097`

Exposed invariant:
`mmap.flush(offset, size)` was called at unaligned offsets (4, 8, 12, ...), causing Linux `EINVAL`.

Repair:
`c89fec2940537f610ee517885c1d9e813d79f3c6`

Only change:
remove per-field `mmap.flush()` from shared-latch writes.

Shared MAP_SHARED visibility does not require msync/flush for this in-memory synchronization path.

Scientific worker, analyzer, thresholds, arm definitions, and launch design are unchanged.

Next:
read repair CI exactly once.

Hosted research only.
No local-PC execution.
