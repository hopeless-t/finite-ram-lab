# REC-003 Residency Observer Footprint Result v1

> **Status:** PASS / OBSERVER-SIZE EFFECT DETECTED
> **Run:** `36442276245`
> **Launch commit:** `ce6866a92fc22bd09145c9837b1208023f801004`
> **Aggregate artifact:** `REC-003-RESIDENCY-OBSERVER-36442276245`
> **Artifact id:** `10979321979`
> **Artifact digest:** `sha256:3333c7313be9b1d83699122e237a9af65d092c1ba70d02e9e7da995da790080e`

## Validity

12 / 12 observer-only trials PASS.

Design matrix:
- 96 / 192 / 384 MiB
- 4 fresh systemd units per size
- no streaming workload
- no hot anonymous allocation
- cold file residency remained 0

## Main result

Median cgroup-current deltas:

| target | mincore vec | max observed | post cleanup | post GC settle |
| --- | ---: | ---: | ---: | ---: |
| 96 MiB | 24 KiB | 0 | 0 | 0 |
| 192 MiB | 48 KiB | 0 | 0 | 0 |
| 384 MiB | 96 KiB | 256 KiB | 254 KiB | 252 KiB |

All four 384 MiB trials showed approximately 256 KiB of cgroup-current growth by/after the mincore-vector phase. The effect persisted through cleanup and the short GC settle.

At 192 MiB, 1/4 trials showed +256 KiB while 3/4 remained at zero. At 96 MiB, 4/4 remained zero.

The observed allocation step is therefore coarse/granular rather than equal to the logical mincore vector size.

## Causal interpretation

The residency observer itself has a target-size-dependent cgroup footprint under the tested Python/glibc/cgroup environment.

This is sufficient to reject a pure-workload interpretation of the earlier sub-MiB post-scan floor growth.

The earlier STRATA capacity series showed roughly +0.2421875 MiB median floor growth per doubling. REC-003 independently produces a ~0.25 MiB observer allocation step at the 384 MiB target.

Do not claim exact numerical identity: allocator/cgroup charging is quantized and the 192 MiB observer cell is mixed (1/4 positive). But the magnitude and size dependence are directly compatible with observer contamination.

## What survives

The main STRATA knee result survives because the MemoryHigh response is measured during the streaming scan, before the post-scan residency observer.

Across 96 / 192 / 384 MiB:

`80 < K <= 88 MiB`

remains the accepted empirical result.

Thus the strongest current statement is:

`instantaneous RAM demand ~= effective live set + unreleased streaming interval + bounded overhead`

for the tested one-shot streaming workload, while total dataset capacity is not itself the instantaneous demand.

## Pseudo-Council convergence

- **Measurement:** observer contamination is real at 384 MiB; fine post-scan floor values are not pure workload measurements.
- **Systems:** the ~256 KiB step is consistent with coarse allocator/cgroup charging; it is not evidence that mmap populated the file cache.
- **Statistics:** 4/4 positive at 384, 0/4 at 96, mixed 1/4 at 192 is directional evidence, not a smooth scaling law.
- **Finite-RAM:** retain the 8 MiB knee interval; demote the sub-MiB floor-growth pattern.
- **OSS:** future floor measurements should occur before residency observation or in a separate observer process/cgroup.
- **Authority:** no controller/default cadence follows.

Consensus:

**REC-003 resolves the fine-floor HOLD as measurement contamination. Preserve the capacity-decoupled knee; retire the sub-MiB floor-growth sequence as a candidate workload law.**

## Next research direction

Measurement hygiene first:

1. define a pre-observer floor sample;
2. optionally move mincore residency checks into a separate cgroup/process;
3. quantify whether this changes any reported non-hot-floor summaries;
4. then resume external-validity work on throughput cost and portability.

Hosted research only. No local-PC execution. No memory-control policy.
