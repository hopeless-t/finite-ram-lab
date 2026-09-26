# VAL-001 Design Monte Carlo Finding

> **Status:** DESIGN DECISION SUPPORT  
> **Run:** 36219282588

## Question

Which boundary-refinement design should be used to validate the CHAR-001 transition across independent GitHub-hosted runners?

## Monte Carlo

Four blocked designs were stressed under four declared nuisance scenarios:

- sharp transition;
- moderate transition;
- broad transition;
- noisy/non-monotonic pressured regime.

Each design/scenario pair used 5,000 simulated experiments.

The simulation included runner-wide variation, trial noise, level-specific pressured-side variation, and a latent boundary drawn between 162 and 190 MiB.

## Result

| Design | Trials | Worst P95 boundary error | Worst within ±4 MiB |
| --- | ---: | ---: | ---: |
| D1_COARSE_BLOCKED | 120 | 8.23 MiB | 0.638 |
| D2_FINE_BALANCED | 108 | 7.06 MiB | 0.689 |
| D3_FINE_REPLICATED | 144 | 7.02 MiB | 0.695 |
| D4_ULTRAFINE_LIGHT | 136 | 6.54 MiB | 0.668 |

Pareto set for trial count versus worst-case P95 localization error:

```text
D2_FINE_BALANCED
D4_ULTRAFINE_LIGHT
```

## Pseudo-Council conclusion

D2 is selected for VAL-001.

Reasons:

1. it is Pareto-efficient;
2. it uses fewer trials than D4;
3. D4 spends 28 additional trials for only about 0.52 MiB improvement in the simulated worst-case P95 localization error;
4. D2 uses six independent runner blocks versus four in D4, which better serves the actual validation question: cross-runner reproducibility;
5. if 4 MiB spacing proves insufficient, a later adaptive refinement can target only the surviving interval.

No arbitrary weighted score was used.

## Frozen VAL-001 design

```text
MemoryHigh levels:
160, 164, 168, 172, 176, 180, 184, 188, 192 MiB

Independent runner blocks:
6

Repeats per level inside each block:
2

Total controlled trials:
108
```

Each runner block executes all levels in a deterministically shuffled order.

The Monte Carlo is design support only. It does not establish the real boundary.
