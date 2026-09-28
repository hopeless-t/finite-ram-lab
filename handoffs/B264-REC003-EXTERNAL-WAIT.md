# Bounce Handoff

> **Bounce ID:** B264
> **Status:** EXTERNAL_WAIT / REC-003 HOSTED RUN IN PROGRESS

Exact launch commit:

`ce6866a92fc22bd09145c9837b1208023f801004`

Scientific run:

`36442276245`

Single status read in B264:

`in_progress`

No second read was performed.

REC-003 frozen execution:
- observer-only
- sizes 96 / 192 / 384 MiB
- 4 blocks
- 12 trials
- fresh systemd unit per size
- no streaming workload
- no hot anonymous allocation
- mmap / ctypes / mincore phase snapshots
- memory.current + selected memory.stat
- final memory.peak

Next fresh bounce: read run `36442276245` exactly once.

Success -> fetch aggregate once, validate 12 trials, determine transient vs retained observer footprint, and resolve the sub-MiB floor HOLD.
Pending -> EXTERNAL_WAIT.
Failure -> inspect only the exposed invariant.

Hosted research only. No local-PC execution. No memory-control policy.
