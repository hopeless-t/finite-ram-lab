# CURRENT

> **Latest bounce:** B263
> **Stage:** REC-003 / EXPLICIT HOSTED LAUNCH
> **Turn stop reason:** RUN_DISCOVERY_PENDING

Implementation CI `36441838606`: completed / success.

Exact launch commit:

`ce6866a92fc22bd09145c9837b1208023f801004`

REC-003 frozen execution:

- file sizes 96 / 192 / 384 MiB
- 4 blocks
- 12 observer-only trials
- fresh systemd unit per size
- no streaming workload
- no hot anonymous allocation
- mmap / ctypes / mincore phase snapshots
- memory.current + selected memory.stat
- final memory.peak

Question: is the sub-MiB floor growth partly caused by the residency observer itself?

Next fresh-bounce action: discover/read REC-003 for exact launch commit once.

Hosted research only. No local-PC execution. No memory-control policy.
