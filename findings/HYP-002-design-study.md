# HYP-002 Design Monte Carlo Finding

> **Status:** DESIGN DECISION SUPPORT  
> **Run:** 36242981650

## Question

How many independent runner blocks are needed to test whether randomized pre-burst recency/order determines matched-region residency at 160–162 MiB?

## Empirical design input

The design study used the exploratory OBS-003 pooled 160/162 MiB runner-block recency contrast as a residual model:

```text
mean recent-minus-older residency contrast = 0.07136
SD                                      = 0.05598
n                                       = 32 blocks
```

The simulation attenuated the mean effect to 100%, 75%, 50%, and 35%.

This input is design support only.

## Candidate designs

| Design | Blocks | Trials | Detect @100% | @75% | @50% | @35% | P90 error @50% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D1_8 | 8 | 64 | 0.977 | 0.846 | 0.712 | 0.521 | 0.02983 |
| D2_12 | 12 | 96 | 0.999 | 0.971 | 0.757 | 0.607 | 0.02484 |
| D3_16 | 16 | 128 | 1.000 | 0.995 | 0.918 | 0.658 | 0.02178 |
| D4_20 | 20 | 160 | 1.000 | 0.999 | 0.944 | 0.709 | 0.01961 |

The design-screen detection statistic is a one-sided block-level t proxy.

Final HYP-002 inference will not use that proxy; it will use exact runner-block sign-flip randomization.

## Pseudo-Council conclusion

Select **D3_16**.

Reasons:

1. the pre-declared selection target was >=90% screened detection at 50% of the exploratory effect;
2. D3 is the smallest design to cross that target;
3. D4 adds 32 trials for a modest increase from 0.918 to 0.944 at the half-effect screen;
4. 16 independent blocks permit exact enumeration of all `2^16 = 65,536` sign assignments;
5. the factorial design already provides eight balanced cells per block.

## Frozen HYP-002 design

```text
16 independent runner blocks

per block:
  MemoryHigh      160 / 162 MiB
  recent_identity A / B
  future HOT      A / B

2 x 2 x 2 = 8 cells / block

total trials:
16 x 8 = 128
```

No application hint or memory-management intervention is used.

## Primary inference

Per runner block:

```text
mean(recent resident fraction - older resident fraction)
```

Primary directional hypothesis:

```text
recent > older
```

Use exact one-sided sign-flip randomization over 16 runner-block contrasts.

Also report a runner-cluster bootstrap interval for the mean residency contrast.

## Key secondary inference

Because future HOT identity is randomized independently:

```text
aligned    = HOT == recent
misaligned = HOT == older
```

Compare block-level mean log HOT-retouch latency:

```text
misaligned - aligned
```

with exact sign-flip randomization as a pre-registered secondary diagnostic.

## Authority boundary

The design study does not establish that recency controls reclaim or that future semantic information has performance value.
