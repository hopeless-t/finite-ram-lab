# OBS-002 Initial Finding

> **Status:** STRONG OBSERVATIONAL ASSOCIATION / OBSERVER EFFECT NOT YET CLEARED  
> **Run:** 36220164283  
> **Source commit:** `a7611d9e01160676690e593ac52205a0f7c3f795`

## Design

OBS-002 used:

- 8 independent GitHub-hosted runner blocks;
- anonymous private `mmap` regions for hot set and burst;
- `mincore(2)` page-residency snapshots;
- 160 MiB control × 1 per block;
- 164 MiB transition zone × 4 per block;
- 168 MiB control × 1 per block.

Total valid trials: 48.

All execution checks passed, `mincore` worked on every trial, and no OOM occurred.

## Endpoint control reproduction

The instrumented `mmap + mincore` workload preserved the broad endpoint separation seen previously.

### 160 MiB

Across 8 independent controls:

- median hot-set residency after burst: about 96.0%;
- median retouch latency: about 586 ms;
- median retouch swap-ins: about 16.2k pages.

### 168 MiB

Across 8 independent controls:

- hot-set residency after burst: 100%;
- median retouch latency: about 3.96 ms;
- median retouch swap-ins: 0.

The qualitative pressured/unpressured split therefore survived the allocator/instrumentation change at the endpoint controls.

## Transition-zone relationship at 164 MiB

There were 32 transition-zone trials.

Primary relationship:

```text
hot-set resident fraction immediately after BURST_ALLOC
            versus
HOTSET_RETOUCH latency
```

Observed Spearman correlation:

```text
rho = -0.8612
```

A 100,000-draw within-runner blocked permutation test gave:

```text
two-sided p ≈ 3.0e-5
```

A 5,000-resample cluster bootstrap over whole runner blocks gave:

```text
median rho ≈ -0.856
95% interval ≈ [-0.927, -0.740]
```

Supporting relationship:

```text
hot-set missing pages after BURST_ALLOC
            versus
anonymous swap-ins during HOTSET_RETOUCH
```

Observed Spearman:

```text
rho = 0.8999
blocked permutation p ≈ 3.0e-5
```

Within this instrumented workload, region identity is therefore much more informative than aggregate memory usage alone.

## Discrete residency pattern

The 164 MiB trials often fell into clear page-residency groups.

Examples included:

- 0 hot-set pages missing -> roughly 4 ms retouch;
- about 140 pages missing -> roughly 13–25 ms;
- about 500 pages missing -> roughly 23–25 ms.

This pattern is consistent with the idea that the cost of the next application phase depends on whether pages from the soon-reused semantic region remain resident.

## Important difference from VAL-001

The earlier bytearray-based VAL-001 transition zone contained rare extreme retouches up to about 2.76 seconds.

OBS-002 did **not** reproduce that extreme tail at 164 MiB; its 164 MiB retouches ranged from about 3.8 to 25.8 ms.

Therefore the instrumentation/allocation change affected the transition-zone dynamics even though the 160 and 168 MiB endpoint regimes remained qualitatively stable.

This prevents promotion of the region-residency association directly into a mechanism finding.

## Observer-effect concern

The `mincore` calls themselves were measured.

Across the critical residency calls:

- median duration: about 23.7 microseconds;
- p95: about 2.60 ms;
- maximum: about 3.57 ms.

Those upper-tail observation costs are not negligible relative to a fast 4–25 ms transition-zone retouch.

In addition, the `mincore(2)` interface provides only a snapshot; Linux documentation explicitly notes that residency can change immediately after the call.

## Deeper-pressure clue

At 160 MiB, the hot set was still about 96% resident immediately after `BURST_ALLOC`, yet the following retouch produced a median of roughly 16k swap-ins.

This suggests that deep-pressure cost is not explained only by pages already missing before retouch.

A second process may be occurring during the retouch itself: touching the hot set while the cgroup remains under heavy reclaim pressure may cause continuing eviction/refault churn.

That is a new candidate, not yet a finding.

## Council conclusion

OBS-002 supports a **Region Residency Identity** hypothesis:

> Near the pressure boundary, the future cost of an application phase is strongly associated with whether pages belonging to the soon-reused semantic region remain resident.

But the observation method may alter the transition zone.

The next experiment must therefore be **VAL-002 — Observer-Effect Validation**:

- same anonymous `mmap` allocator;
- randomized paired trials;
- pre-retouch `mincore` ON versus OFF;
- focus on 164 MiB;
- preserve 160/168 controls;
- compare latency, swap, reclaim, and fault distributions.

No application hint or memory-policy intervention is authorized until the observer effect is bounded.
