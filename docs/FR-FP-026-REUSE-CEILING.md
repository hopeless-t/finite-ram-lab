# FR-FP-026 — Reuse-probability ceiling

Status: **ANALYTIC REDUCTION CANDIDATE**

Parent: **FR-FP-025**

## Why

FR-FP-025 treated reuse probability p as an external point input.

A point estimate may be harder to obtain than the decision actually requires.

Both FR-FP-025 constraints are linear in p.

That means the decision can be inverted.

## Expected-cost bound

FR-FP-025 requires:

    lambda
      >=
    p * E[(bR-W)+] / 8 MiB

Therefore:

    p
      <=
    8 MiB * lambda
      /
    E[(bR-W)+]

## Deadline-risk bound

FR-FP-025 also requires:

    epsilon
      >=
    p * P(bR>D)

Therefore:

    p
      <=
    epsilon
      /
    P(bR>D)

If the conditional miss probability is zero, this constraint does not limit p.

## Combined decision

Define:

    p_ceiling
      =
    min(
        1,
        cost bound,
        deadline bound
    )

Then COLD is robustly eligible whenever:

    upper_bound(reuse probability)
      <=
    p_ceiling

The Governor does not need an exact reuse point estimate.

It needs a safe upper confidence bound.

## Exact equivalence test

The candidate sweeps:

- the FR-FP-025 baseline grid;
- nine memory shadow prices;
- all four deadlines;
- all four miss tolerances;
- reuse p from 0.05 to 1.00 in 0.05 increments.

For every cell, compare:

1. direct FR-FP-025 eligibility;
2. p <= analytic reuse ceiling.

Qualification requires zero mismatches.

## North-Star consequence

This reduces the next workload-learning problem.

Instead of:

> predict the exact probability that this state will be reused

the Governor can ask:

> can I prove that reuse probability is below this decision-specific ceiling?

That can later be supplied by a conservative recency/frequency model, confidence
sequence, application hint, or observed reuse trace.

The required resident state is smaller and the estimation target is easier.

## Claim ceiling

**ANALYTIC_REDUCTION_OF_FR_FP_025_EMPIRICAL_8MIB_FRONTIER_ONLY**
