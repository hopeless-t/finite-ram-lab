# CURRENT

> **Latest bounce:** B260
> **Stage:** REC-003 RESIDENCY OBSERVER FOOTPRINT DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## Canonical scientific state

STRATA-009 run `36440093666`: PASS, 20/20.

Capacity series 96 / 192 / 384 MiB retains the same:

`80 < K <= 88 MiB`

including 384 MiB > MemoryMax 320 MiB.

## Fine-floor HOLD

The measured post-scan non-hot floor rises slightly with cold capacity.

But `_file_residency()` mmaps the full file and runs mincore before post-scan memory.current is captured.

Do not interpret the small floor trend as a workload law yet.

## REC-003 frozen design

Observer-only file sizes:

- 96 MiB
- 192 MiB
- 384 MiB

Fresh systemd unit per trial, 4 blocks per size, 12 trials total.

Phase snapshots:

- baseline
- mmap
- ctypes view
- mincore vector
- post-mincore
- post-count
- post-cleanup
- post-gc-settle

Capture memory.current, selected memory.stat, and memory.peak.

No streaming workload.
No hot anonymous allocation.

Design:

`docs/REC-003-RESIDENCY-OBSERVER-FOOTPRINT-v1.md`

## Next fresh-bounce action

Implement REC-003:

- spec
- observer instrumentation module
- Ubuntu 26.04 workflow
- aggregate
- tests

Do not launch during implementation.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
Proposal != Decision.
Expressibility != Executability.
