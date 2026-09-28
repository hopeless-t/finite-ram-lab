# CURRENT

> **Latest bounce:** B266
> **Stage:** REC-004 PRE/POST OBSERVER HYGIENE DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## Accepted mechanism

Capacity-series knee:

- 96 MiB -> `80 < K <= 88`
- 192 MiB -> `80 < K <= 88`
- 384 MiB -> `80 < K <= 88`

384 MiB exceeds MemoryMax 320 MiB and completes without OOM under bounded DONTNEED streaming.

## REC-003

Observer-only audit PASS.

Residency observer has a target-size-dependent cgroup footprint, especially at 384 MiB.

The historical fine floor-growth sequence is measurement-contaminated and no longer a workload-law candidate.

## REC-004 frozen design

Paired hygiene validation:

- Ubuntu 26.04
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- DONTNEED 64 MiB
- cold capacities 96 / 192 / 384 MiB
- 4 blocks
- 12 trials

Each trial captures:

1. `post_scan_pre_observer`
2. existing `_file_residency()`
3. `post_scan_post_observer`

Primary paired metric:

`observer_current_delta = post - pre`

Design:

`docs/REC-004-PREPOST-OBSERVER-HYGIENE-v1.md`

## Next fresh-bounce action

Implement REC-004:
- hygienic workload wrapper / variant
- spec
- deterministic schedule
- aggregate
- Ubuntu 26.04 workflow
- tests

Do not launch during implementation.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
Proposal != Decision.
Expressibility != Executability.
