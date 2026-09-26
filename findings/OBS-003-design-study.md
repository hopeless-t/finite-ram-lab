# OBS-003 Design Monte Carlo Finding

> **Status:** DESIGN DECISION SUPPORT  
> **Run:** 36242326971

## Question

How should the lab sample the natural NO_HINT residency-misalignment curve across the 160–168 MiB memcg transition region?

## Monte Carlo

Each candidate was stressed with 10,000 simulated experiments under four declared transition/runner-heterogeneity scenarios.

Five MemoryHigh levels were fixed:

```text
160, 162, 164, 166, 168 MiB
```

Candidate designs:

| Design | Blocks | Repeats/level | Trials |
| --- | ---: | ---: | ---: |
| D1_12x4 | 12 | 4 | 240 |
| D2_16x4 | 16 | 4 | 320 |
| D3_24x3 | 24 | 3 | 360 |
| D4_32x2 | 32 | 2 | 320 |

## Results

| Design | Trials | Worst P90 abs error @164 | Worst P90 curve MAE | Worst median cluster-CI width @164 | Worst P(>=6 affected blocks @164) |
| --- | ---: | ---: | ---: | ---: | ---: |
| D1_12x4 | 240 | 0.1482 | 0.0945 | 0.3508 | 0.665 |
| D2_16x4 | 320 | 0.1279 | 0.0814 | 0.3083 | 0.919 |
| D3_24x3 | 360 | 0.1157 | 0.0717 | 0.2703 | 0.980 |
| D4_32x2 | 320 | 0.1123 | 0.0689 | 0.2640 | 0.971 |

Pareto set:

```text
D1_12x4
D4_32x2
```

## Pseudo-Council conclusion

Select **D4_32x2**.

Reasons:

1. D4 is Pareto-efficient;
2. it uses the same 320-trial budget as D2 but provides more independent runner blocks and lower simulated estimation error;
3. compared with D1, the additional 80 trials materially improve worst-case 164 MiB prevalence error and affected-runner coverage;
4. D3 spends 40 more trials than D4 while being slightly worse on the declared worst-case error metrics;
5. the scientific question is specifically about runner-replicated natural opportunity, so independent blocks are more valuable than dense within-run repetition.

No weighted overall score was used.

## Frozen OBS-003 design

```text
MemoryHigh levels:
160, 162, 164, 166, 168 MiB

Independent runner blocks:
32

Repeats per level per block:
2

Total trials:
320

Intervention:
none / NO_HINT only
```

## Primary quantity

For each level:

```text
P(HOT resident fraction < 1.0 immediately before reuse)
```

Runner block remains the top-level replication unit.

## Authority boundary

This simulation chooses a sampling design.

It does not establish the real misalignment curve or performance value of any intervention.
