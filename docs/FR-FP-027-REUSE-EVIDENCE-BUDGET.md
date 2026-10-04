# FR-FP-027 — Reuse evidence budget

Status: **ANALYTIC EVIDENCE-BUDGET CANDIDATE**

Parent: **FR-FP-026**

## Why

FR-FP-026 removed the need for an exact reuse-probability point estimate.

The Governor only needs to prove:

    reuse upper bound <= decision-specific reuse ceiling

FR-FP-027 converts that ceiling into a sample budget.

## Statistical contract

Treat each stable-window reuse opportunity as a Bernoulli observation:

    reused = 1
    not reused = 0

Use a one-sided exact Clopper-Pearson upper confidence bound.

The result is deliberately conservative.

## Zero observed reuse

If n observations contain zero reuse events, the exact one-sided upper bound is:

    p_U
      =
    1 - (1-confidence)^(1/n)

At 95% confidence:

- p ceiling 0.50 -> 5 zero-reuse observations;
- p ceiling 0.25 -> 11 observations;
- p ceiling 0.10 -> 29 observations;
- FR-FP-026 slow/strict ceiling ~0.0833 -> 35 observations.

At 99% confidence the required evidence increases.

## General observed reuse

For x reuse events in n observations:

    p_U
      =
    BetaQuantile(
        confidence,
        x + 1,
        n - x
    )

The candidate tabulates minimum n for x = 0, 1, 2.

Observed reuse increases the evidence required before COLD can be certified.

## Governor stop rule

The workload learner can now be sequential:

1. compute the current FR-FP-026 reuse ceiling;
2. observe reuse opportunities;
3. update the exact upper confidence bound;
4. stop observing once:

       p_upper <= reuse_ceiling

5. if the evidence budget is not met, keep WARM or choose another policy.

This is decision-directed measurement.

The system does not collect an arbitrarily large reuse trace before asking what
decision it needs to make.

## Important assumption

This lane assumes a stable Bernoulli decision window.

It does not establish that real application reuse is iid, stationary, or
exchangeable.

A later physical/application trace must test those assumptions.

## North-Star consequence

The unresolved workload problem has been reduced again:

    exact reuse predictor
      -> reuse upper bound
      -> exact evidence budget

The Governor can ask for only as much evidence as the current tier decision
requires.

## Claim ceiling

**EXACT_BINOMIAL_EVIDENCE_BUDGET_UNDER_STABLE_BERNOULLI_REUSE_ASSUMPTION_ONLY**
