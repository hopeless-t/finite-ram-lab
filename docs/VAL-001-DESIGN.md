# VAL-001 Design Council

> **Status:** DESIGN STUDY IN PROGRESS

## Decision question

CHAR-001 found a reproducible regime transition between the sampled 160 MiB and 192 MiB `MemoryHigh` conditions.

Before running VAL-001, choose a boundary-refinement design that is robust to hosted-runner noise without spending trials on false precision.

## Pseudo-Council positions

### Kernel / VM reviewer

Use independent hosted runners. A boundary seen on one VM must not become a Linux claim.

### Performance reviewer

Use a paired/block design: each runner should observe several `MemoryHigh` levels so runner-wide speed differences do not dominate the comparison.

### Statistician

Analyze latency on a log-like scale and treat runner identity as a block. Do not pool all trials as if they were independent.

### Experimental scientist

Refine the boundary, but do not jump directly to 1 MiB spacing. The previous grid only localized the transition to a 32 MiB interval.

### Falsification reviewer

VAL-001 must be allowed to show that the boundary is unstable, runner-dependent, broad, or absent.

### Monte Carlo reviewer

Compare candidate level grids and runner/repeat allocations under several nuisance scenarios before spending hosted-runner trials.

## Candidate designs

The design Monte Carlo compares:

- **D1_COARSE_BLOCKED:** 5 levels × 8 independent runner blocks × 3 repeats;
- **D2_FINE_BALANCED:** 9 levels at 4 MiB spacing × 6 blocks × 2 repeats;
- **D3_FINE_REPLICATED:** same 9 levels × 8 blocks × 2 repeats;
- **D4_ULTRAFINE_LIGHT:** 17 levels at 2 MiB spacing × 4 blocks × 2 repeats.

No weighted overall score is used.

The primary design trade-off is:

```text
hosted-runner trial count
        versus
worst-case boundary localization error
```

The script reports the Pareto set instead of declaring a winner.

## Simulated nuisance scenarios

The design study intentionally includes:

- sharp transition;
- moderate transition width;
- broad transition width;
- noisy/non-monotonic pressured regime;
- runner-wide multiplicative variation;
- per-trial variation.

These are stress models, not fitted claims about the real GitHub runner.

## Council decision rule

After the design Monte Carlo:

1. reject designs that are dominated in both trial cost and worst-case P95 localization error;
2. prefer the lower-cost Pareto design unless the more expensive design buys a materially smaller error that changes the next research decision;
3. if all candidates are fragile under the broad/noisy scenarios, redesign VAL-001 instead of forcing a result.

Only after this decision is frozen should the multi-runner validation workflow be launched.
