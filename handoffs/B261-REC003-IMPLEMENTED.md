# Bounce Handoff

> **Bounce ID:** B261
> **Status:** COMPLETE / REC-003 IMPLEMENTED / NOT LAUNCHED

Implemented observer-only residency-footprint audit:

- spec
- deterministic per-block size schedule
- exact mmap/ctypes/mincore phase instrumentation
- memory.current + selected memory.stat snapshots
- fresh systemd unit per size
- aggregate validator
- Ubuntu 26.04 workflow
- regression tests

Frozen budget: 96/192/384 MiB x 4 blocks = 12 trials.

No launch marker exists.

Next: read ordinary CI exactly once. Success permits a separate explicit REC-003 launch.

Hosted research only.
