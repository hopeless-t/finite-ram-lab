# FR-CLM-001D — Trajectory Survival Under Repeated Context Rewrites

Status: **SYNTHETIC TRAJECTORY QUALIFICATION**

## Goal

FR-CLM-001C showed that resident semantic capacity can compensate for imperfect
selection in a one-step synthetic task.

FR-CLM-001D asks whether that result survives repeated context rewrites.

The core distinction is:

`one-step success != trajectory survival != endpoint success`.

## Trajectory model

Each trajectory starts with two required state variables:

- `goal=g0`
- `constraint=c0`

At every step:

1. the previous resident working set is carried forward;
2. two new distractor events arrive;
3. the selector rewrites the resident set to a fixed budget.

Every eight steps, both required keys receive a new version before selection.

A required fact that was previously lost cannot reappear from hidden full
history. It can recover only when a later refresh explicitly reintroduces it.

That makes eviction persistent but not necessarily permanent.

## Selector

The selector reuses the FR-CLM-001C relevance-label model:

- true relevant = newest candidate event for each required key;
- every candidate label flips with probability 0.01;
- predicted-relevant events rank first;
- recency breaks ties.

Pseudo-random draws are deterministic under hash domain:

`TRAJECTORY_SCORE_FLIP`.

The draw identity excludes requested trajectory length, so a 32-step trajectory
is the exact prefix extension of the same replicate's 1/2/4/... step cells.

## Frozen sweep

Resident budgets:

`2, 4, 6`

Trajectory lengths:

`1, 2, 4, 7, 8, 9, 15, 16, 17, 31, 32`

Replicates per budget:

`2,048`

Refresh interval:

`8 steps`

## Primary endpoints

### Trajectory survival

Fraction of trajectories for which **every** step through L is semantically
exact.

### Endpoint success

Fraction whose final step at L is exact, regardless of earlier failure.

### Endpoint masking gap

`endpoint success - trajectory survival`

A large positive gap means final-state evaluation is hiding earlier semantic
failure and recovery.

## Secondary endpoints

- mean per-step exact rate;
- first-failure histogram;
- recovered-trajectory count;
- first-failure biopsy;
- cold-start independent projection.

The cold-start projection is:

`one_step_survival ^ L`

and is deliberately treated as a naive comparator rather than a valid model.

## Frozen falsifiers

The run fails qualification if:

- trajectory survival increases with length for a fixed budget;
- budget 4 or 6 is not exact at the one-step cold start;
- length-32 survival does not order as budget2 < budget4 < budget6;
- budget 4 length-32 survival is >= 0.70;
- budget 6 length-32 survival is >= 0.75;
- the endpoint masking gap at length 32 is not large enough;
- refresh-boundary endpoint success falls below 0.95.

These conditions are intentionally broad enough to test the qualitative
trajectory hypothesis without freezing every pseudo-random count.

## Why lengths straddle refresh boundaries

Lengths 7/8/9, 15/16/17, and 31/32 expose phase sensitivity.

If endpoint-only scoring is misleading, endpoint success should jump at refresh
boundaries even though all-steps trajectory survival cannot recover once an
earlier step has failed.

This distinguishes:

`state currently correct`

from:

`trajectory remained semantically valid throughout`.

## Claim ceiling

**SYNTHETIC_TRAJECTORY_SURVIVAL_ONLY**

No real CLM, language model, Pi, KITten worker, or provider is evaluated.

## Next if PASS

FR-CLM-001E should separate error dependence:

- independent per-event rewrite noise;
- temporally correlated bad-state episodes;
- bursty failure regimes.

That would test whether rare correlated failures dominate long-run trajectory
survival even when the one-step marginal error rate is held constant.
