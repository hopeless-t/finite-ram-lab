# EXP-001 Initial Finding

> **Status:** POSITIVE CAUSAL RESULT / BOUNDED INTERVENTION  
> **Run:** 36228194951

## Question

At matched resident-memory quantity and matched reclaim amount, does next-use latency depend causally on which semantic region remains resident?

## Execution

All frozen execution checks passed:

- 8 independent hosted-runner blocks;
- 32 total trials;
- 16 HOT_EVICT and 16 COLD_EVICT trials;
- physical HOT mapping identity balanced A/B;
- no OOM events;
- all content-integrity checks passed.

Intervention fidelity was strong:

    maximum selected-target resident fraction = 0.09375
    minimum non-target resident fraction       = 1.00000

## Primary result

| Arm | Trials | Median HOT retouch | P90 | Median HOT residency | Median retouch swap-ins |
| --- | ---: | ---: | ---: | ---: | ---: |
| COLD_EVICT | 16 | 0.261 ms | 0.397 ms | 1.0000 | 0 pages |
| HOT_EVICT | 16 | 121.647 ms | 756.289 ms | 0.0000 | 4096 pages |

Pre-registered runner-block inference:

    geometric mean latency ratio
    HOT_EVICT / COLD_EVICT = 639.45x

Exact sign-flip over all:

    2^8 = 256 block sign assignments

gave:

    two-sided p = 0.0078125

Cluster-bootstrap ratio interval:

    95% interval = [390.37x, 1125.54x]

## Secondary observation

In HOT_EVICT, the median HOT retouch incurred:

- 4096 swap-ins;
- 4096 anonymous refaults;
- about 520 major faults.

In COLD_EVICT, the HOT region remained fully resident and median retouch swap-ins/refaults/major faults were zero.

These counters are secondary descriptive evidence; the randomized residency-identity intervention is the primary causal evidence.

## Finding

Under the bounded experiment, equal memory quantity is **not** performance-equivalent when residency identity differs relative to imminent application demand.

Making the soon-reused HOT region nonresident caused a very large next-use cost, while reclaiming the equal-size COLD region left HOT reuse fast.

Therefore:

    residency quantity held approximately matched
              +
    reclaim amount held matched
              +
    future workload held matched
              ↓
    residency identity alone is sufficient
    to change next-use performance dramatically

This is a direct causal bridge from the OBS-002 residency association.

## What this establishes

Finite RAM performance can depend strongly on **alignment between residency identity and future demand**, not only on the number of resident bytes.

## What this does not establish

EXP-001 does not show:

- that natural Linux reclaim is globally suboptimal;
- that the kernel could have inferred the future demand from its own available information;
- that `MADV_COLD`, `MADV_PAGEOUT`, or another application hint improves natural pressure behavior;
- that a userspace coordination service is necessary;
- that the observed effect size generalizes beyond this bounded hosted experiment.

## Next research direction

The smallest justified next question is now an information-value intervention:

> Under natural transition-zone pressure, can a minimal existing application semantic hint about the **not-soon-needed** region preserve future-needed residency and reduce the observed next-use cost?

A low-authority existing Linux hint should be tested before designing a new coordination plane.
