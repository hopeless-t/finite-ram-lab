# HYP-001 Design Study

> **Status:** DESIGN DECISION SUPPORT

## Question

How much independent hosted-runner replication is needed for the future-reuse alignment experiment under a deliberately heavy-tailed transition-zone noise model?

## Monte Carlo model

Each simulated experiment included:

- runner-wide log-latency variation;
- per-trial variation;
- rare slow-branch events;
- matched ALIGNED and MISALIGNED arms;
- paired analysis at runner-block level.

The calculation used 5,000 simulated experiments per design/scenario.

This is design support, not Linux evidence.

## Initial candidates

| Design | Transition trials | Null FP | 1.5x detect | 2x detect | Branch-shift detect | Mixed detect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 blocks x4/arm | 64 | 0.052 | 0.128 | 0.290 | 0.210 | 0.270 |
| 8 blocks x6/arm | 96 | 0.051 | 0.169 | 0.396 | 0.298 | 0.378 |
| 12 blocks x4/arm | 96 | 0.055 | 0.184 | 0.428 | 0.313 | 0.391 |
| 12 blocks x6/arm | 144 | about 0.05 | about 0.25 | about 0.60 | about 0.44 | about 0.55 |

At equal 96-trial cost, more independent runner blocks performed better than adding within-runner repeats.

## Extended candidates

| Design | Transition trials | Null FP | 1.5x detect | 2x detect | Branch-shift detect | Mixed detect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 blocks x6/arm | 192 | 0.047 | 0.329 | 0.735 | 0.583 | 0.687 |
| 16 blocks x8/arm | 256 | 0.046 | 0.427 | 0.856 | 0.700 | 0.813 |
| 20 blocks x6/arm | 240 | 0.053 | 0.401 | 0.838 | 0.677 | 0.793 |

## Pseudo-Council conclusion

Select:

```text
20 independent runner blocks
6 repeats per arm at 164 MiB
```

Reasons:

1. independent runner replication is particularly valuable after the large block heterogeneity observed in VAL-002;
2. the 20x6 design is slightly cheaper than 16x8 while retaining similar simulated sensitivity for large/mixed effects;
3. the experiment remains intentionally underpowered for small effects near 1.5x, so a null result must not be interpreted as proof of equivalence;
4. endpoint controls can verify that the split-hotset workload still reaches the intended pressure regimes.

## Frozen warning

A negative HYP-001 result rules out only effects large enough to be visible under this design and workload.

It does not establish that future application information has zero value.
