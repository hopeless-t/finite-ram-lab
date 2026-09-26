# VAL-001 Initial Finding

> **Status:** VALIDATED CHARACTERIZATION / MECHANISM UNRESOLVED  
> **Successful run:** 36219464738  
> **Source commit:** `60d37d0926e0ffc0caea6a4fc01a8226e93d2ad3`

## Design

VAL-001 used the Monte-Carlo-selected D2 design:

- 6 independent GitHub-hosted runner blocks;
- 9 `MemoryHigh` levels from 160 to 192 MiB at 4 MiB spacing;
- 2 repeats per level per runner;
- 108 total controlled trials.

Every execution check passed and no OOM event occurred.

## Cross-runner boundary

Per-runner log-latency step estimates:

| Runner block | Breakpoint estimate | 160/192 latency ratio |
| ---: | ---: | ---: |
| 0 | 162 MiB | 185.6× |
| 1 | 162 MiB | 129.8× |
| 2 | 162 MiB | 149.1× |
| 3 | 162 MiB | 239.3× |
| 4 | 166 MiB | 293.0× |
| 5 | 166 MiB | 204.3× |

A 5,000-resample cluster bootstrap over whole runner blocks produced the discrete-grid breakpoint distribution:

```text
162 MiB: 86.82%
166 MiB: 13.18%
```

with a nominal 95% cluster-bootstrap interval of:

```text
[162, 166] MiB
```

Because the estimator can only choose midpoints of the sampled 4 MiB grid, this interval is a discrete design result rather than a sub-MiB physical confidence bound.

## Stable controls

At 160 MiB all runner blocks were in a strongly pressured regime.

Median across runner-block medians:

- HOTSET_RETOUCH latency: about 519 ms;
- swap growth: about 74.6 MiB;
- `memory.high` events: about 124;
- `pgscan`: about 57,570 pages.

At 168 MiB every runner block was in a low-pressure regime:

- HOTSET_RETOUCH latency: about 3.39 ms;
- cgroup-local swap growth: 0;
- `memory.high` events: 0;
- `pgscan`: 0;
- `pgsteal`: 0.

The same no-reclaim pattern continued through 192 MiB.

## Transition zone at 164 MiB

164 MiB did **not** behave like a smooth midpoint.

Across the 12 individual trials:

- 9 completed HOTSET_RETOUCH in under 10 ms;
- one took about 55.8 ms;
- one took about 254 ms;
- one took about 2.76 s.

All 164 MiB trials showed some pressure during the broader workload, but the amount of reclaim/swap differed sharply between runner blocks.

This makes 164 MiB a stochastic transition zone rather than a single deterministic latency level.

## Exploratory phase-resolved forensics

The raw VAL-001 timelines contain enough phase snapshots to compare `BURST_ALLOC` with the immediately following `HOTSET_RETOUCH`.

This post-hoc analysis is exploratory and was not the pre-registered primary analysis.

At 164 MiB, retouch latency was strongly associated with how much swap/reclaim had already occurred during `BURST_ALLOC`.

Examples:

### Low-latency block

One block reached `BURST_ALLOC` with roughly 6.8–8.2 MiB of cgroup swap.

The subsequent hot-set retouch required only about 40–248 anonymous swap-ins/refaults and completed in about 3.9–8.6 ms.

### High-latency block

Another block reached `BURST_ALLOC` with roughly 47–49 MiB of cgroup swap.

The subsequent hot-set retouch required about 8.6k–8.8k anonymous swap-ins/refaults, over 1,000 major faults, and completed in roughly 254 ms to 2.76 s.

Across the 12 transition-zone trials, exploratory Spearman associations included:

- retouch latency vs swap present after BURST_ALLOC: rho ≈ 0.97;
- retouch latency vs retouch anonymous swap-ins/refaults: rho ≈ 0.86;
- retouch latency vs retouch major faults: rho ≈ 0.90.

These correlations are hypothesis-generating only. The sample is small, multiple relationships were inspected, and no causal claim is authorized.

## Important semantics of the actuator

The experiment uses cgroup v2 `memory.high`.

Linux documents `memory.high` as a **memory usage throttle limit**: exceeding it throttles cgroup processes and puts them under heavy reclaim pressure. It is not a hard physical-RAM capacity boundary, and it does not invoke OOM by itself.

Therefore VAL-001 establishes a reproducible **memcg pressure regime transition** on the hosted environment.

It does not yet establish that the same numeric boundary or dynamics occur under machine-wide physical-RAM exhaustion.

## Candidate mechanism raised by the evidence

The next hypothesis to test is not simply “swap is slow.”

A more specific candidate is:

> Under near-boundary pressure, performance depends strongly on **which semantic region loses residency during the burst**, not only on aggregate memory usage.

If soon-reused hot-set pages are reclaimed during `BURST_ALLOC`, the following `HOTSET_RETOUCH` should expose large swap-in/refault cost.

If other pages are reclaimed while the hot set stays resident, the retouch should remain fast.

This is still a hypothesis.

## Next experiment

OBS-002 should directly observe residency by semantic region.

The preferred observation method is anonymous `mmap` regions plus `mincore(2)` snapshots for:

- hot set;
- burst region.

Before interpreting those observations, the instrumented workload must reproduce the known 160 MiB pressured and 168 MiB unpressured controls.

No hinting, `madvise`, coordinator, or policy intervention is authorized yet.
