# Bounce Handoff

> **Bounce ID:** B260
> **Status:** COMPLETE / REC-003 OBSERVER FOOTPRINT DESIGN FROZEN

STRATA-009 accepted capacity-decoupled knee behavior through 384 MiB > MemoryMax.

Fine post-scan floor growth remains on HOLD because `_file_residency()` itself scales over the whole file.

REC-003 freezes an observer-only audit:

- sizes 96 / 192 / 384 MiB
- fresh systemd unit per trial
- 4 blocks per size
- 12 trials
- no streaming workload
- no hot anon
- phase-level memory.current + memory.stat
- final memory.peak
- explicit cleanup + gc settle

Next: implement REC-003 only. Do not launch in implementation bounce.

Hosted research only.
