# REC-004 Pre/Post Observer Hygiene Result v1

> **Status:** PASS / CLEAN FLOOR BOUNDED / SMOOTH CAPACITY TREND NOT SUPPORTED
> **Run:** `36443845901`
> **Launch commit:** `fc0a3d0b8d221777225d7a4a4ae1e5841a0e2367`
> **Aggregate artifact:** `REC-004-PREPOST-OBSERVER-36443845901`
> **Artifact id:** `10980140275`
> **Artifact digest:** `sha256:549f0b0689bbdab14683452be1e536fa8c302d997f842a859ff98c69cc35de62`

## Validity

- 12 / 12 paired trials PASS
- 96 / 192 / 384 MiB
- 4 blocks per capacity
- DONTNEED 64 MiB
- hot anon 64 MiB
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- no local-PC execution

Cold verification occurred outside the measured transient unit.

Inside the measured unit, the ordering was:

`scan -> post_scan_pre_observer -> _file_residency() -> post_scan_post_observer`

## Aggregate clean floor

Median non-hot floor before the observer:

| cold capacity | pre-observer non-hot floor |
| --- | ---: |
| 96 MiB | 12.6875 MiB |
| 192 MiB | 12.8046875 MiB |
| 384 MiB | 12.935546875 MiB |

Aggregate median span:

`0.248046875 MiB`

All three sizes remained in the same narrow ~12.6–13.1 MiB band.

## Post-observer floor

Median post-observer non-hot floor:

| cold capacity | post-observer non-hot floor |
| --- | ---: |
| 96 MiB | 12.6875 MiB |
| 192 MiB | 12.8046875 MiB |
| 384 MiB | 13.056640625 MiB |

Aggregate median span:

`0.369140625 MiB`

The post-observer span is wider than the clean pre-observer span.

## Paired observer delta

- 96 MiB: 0 / 4 positive observer-current deltas
- 192 MiB: 0 / 4 positive
- 384 MiB: 1 / 4 positive
- the positive 384 MiB paired delta was +256 KiB

The paired result directionally agrees with REC-003 that the residency observer can add a coarse target-size-dependent cgroup charge.

The effect is not deterministic in every trial.

## Block-level clean-floor behavior

The clean pre-observer floor is not monotonic with capacity in every block.

Examples:

- block 0: 12.566 -> 12.809 -> 12.816 MiB
- block 1: 12.563 -> 12.813 -> 13.055 MiB
- block 2: 12.809 -> 12.563 -> 12.813 MiB
- block 3: 13.055 -> 12.801 -> 13.059 MiB

Therefore the small aggregate median increase must not be promoted to a smooth capacity law.

The observed clean values are consistent with a bounded floor plus coarse allocator/cgroup accounting variation and runner jitter.

## Scan behavior

All 12 trials had:

- zero MemoryHigh events at DONTNEED 64 MiB;
- file post-residency fraction 0;
- no scientific invalidation.

The capacity-decoupled streaming conclusion remains intact.

## Measurement-contract decision

Prospective studies should:

1. use `post_scan_pre_observer` as the workload-floor quantity;
2. label historical post-scan floor summaries as legacy post-observer measurements where relevant;
3. keep `post_scan_post_observer` only as a diagnostic;
4. perform cold/residency verification outside the measured cgroup when possible;
5. never rewrite historical raw evidence.

## Pseudo-Council convergence

- **Measurement:** pre-observer floor is the correct prospective workload-floor measurement.
- **Statistics:** no robust monotonic clean-floor scaling law is established across 96/192/384 MiB.
- **Systems:** ~256 KiB observer steps and ~4 KiB-aligned clean-floor jitter are compatible with allocator/cgroup charging granularity.
- **Finite-RAM:** the 80–88 MiB knee and dataset-capacity decoupling remain accepted.
- **Evidence:** historical raw data stays immutable; semantics are corrected prospectively.
- **Authority:** no controller/default cadence follows.

Consensus:

**Adopt pre-observer floor measurement prospectively. Treat the clean floor as bounded over the tested capacity range, not as a smooth capacity-scaling law.**

## Next research direction

The next high-information move is to convert the accumulated evidence into a queryable cross-experiment corpus, then use SQL to search for stable relations and counterexamples across:

- MemoryHigh
- hot live set
- cold capacity
- runner image
- release cadence
- MemoryHigh events
- scan peak
- clean/post-observer floor
- observer delta
- OOM state

This should support explicit hypothesis generation before new physical experiments.

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default cadence or memory controller authorized.
