# CURRENT

> **Latest bounce:** B259
> **Stage:** STRATA-009 PASS / DATASET CAPACITY DECOUPLED ACROSS MEMORYMAX
> **Turn stop reason:** READY_FOR_OBSERVER_AUDIT_DESIGN

## STRATA-009 PASS

Run `36440093666`, 20/20 trials.

Cold dataset:

`384 MiB > MemoryMax 320 MiB`

Yet all bounded-policy arms completed without OOM.

Onset:

`80 < K <= 88 MiB`

This matches the 96 MiB and 192 MiB capacity studies.

Capacity series:

- 96 MiB -> `80 < K <= 88`
- 192 MiB -> `80 < K <= 88`
- 384 MiB -> `80 < K <= 88`

Leading mechanism:

`instantaneous RAM demand ~= effective live set + unreleased streaming interval`

for the tested one-shot streaming workload.

## Fine-floor HOLD

192->384 empirical bootstrap:

- median shift +0.2421875 MiB
- 95% interval approximately [+0.023438, +0.376953] MiB

But `_file_residency()` mmaps the full target and calls `mincore` before post-scan memory.current is captured.

The small floor shift may therefore include observer footprint.

Do not claim a floor-growth law yet.

## Next fresh-bounce action

Freeze an observer-only residency-footprint design:

- Ubuntu 26.04
- file sizes 96 / 192 / 384 MiB
- no streaming workload
- measure cgroup memory.current around `_file_residency()`
- distinguish transient peak from retained post-call delta
- repeat across independent blocks
- preserve environment receipt

No launch in the design bounce.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
Proposal != Decision.
Expressibility != Executability.
