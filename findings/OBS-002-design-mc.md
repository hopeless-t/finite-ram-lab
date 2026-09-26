# OBS-002 Design Monte Carlo Finding

> **Status:** DESIGN DECISION SUPPORT  
> **Run:** 36219935703

## Input

VAL-001 produced 12 transition-zone trials at 164 MiB.

Using a post-hoc descriptive marker of `HOTSET_RETOUCH > 50 ms`, 3 of 12 trials entered the severe branch.

That threshold is used only for observation-effort planning.

It is **not** an OBS-002 scientific acceptance criterion.

## Posterior-predictive design simulation

A uniform `Beta(1,1)` prior combined with the 3/12 observation gives a `Beta(4,10)` posterior for the descriptive severe-branch probability.

500,000 posterior-predictive draws compared:

| Design | Independent blocks | 164 trials | Total 160/164/168 trials | P(>=2 severe) | P(>=3 severe) |
| --- | ---: | ---: | ---: | ---: | ---: |
| O1_LIGHT | 6 | 18 | 30 | 0.916 | 0.818 |
| O2_BALANCED | 8 | 32 | 48 | 0.980 | 0.951 |
| O3_HEAVY | 10 | 40 | 60 | 0.990 | 0.973 |

## Pseudo-Council conclusion

Select **O2_BALANCED**.

Reasons:

- 8 independent runner blocks strengthen replication;
- 32 transition-zone trials give about 95% posterior-predictive probability of observing at least three severe-branch events under the current uncertainty;
- O3 spends 12 more hosted trials for only about 2.2 percentage points of additional probability for that design-support target;
- one 160 MiB and one 168 MiB control per block test whether the instrumented `mmap + mincore` workload still reproduces the established pressured/unpressured controls.

Frozen OBS-002 effort:

```text
8 independent runner blocks

per block:
  160 MiB x 1
  164 MiB x 4
  168 MiB x 1

total:
  48 trials
```

The scientific analysis will use continuous residency, fault, swap, and latency measurements rather than the >50 ms design marker.
