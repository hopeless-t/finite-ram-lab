# FR-FP-023 — Baseline-normalized residual tail prior

Status: **REUSED EVIDENCE RESIDUAL-TAIL CANDIDATE**

Parent: **FR-FP-022**

## Why

FR-FP-021 and FR-FP-022 separated two questions:

1. what is the current run's COLD restore baseline?
2. how much residual upward tail risk remains around that baseline?

FR-FP-023 tests whether this separation improves prediction.

## Factorization

Use the first current-run 8 MiB COLD restore as baseline:

    b

Represent later restore latency as:

    L = b * R

where:

    R = residual multiplier

For each held-out run, the other fourteen runs supply two competing priors.

RAW
: pooled future restore latency in milliseconds.

NORMALIZED
: pooled future residual multipliers.

The held-out run's current baseline b is never used to build its prior.

## Deadline risk

For an absolute deadline D:

RAW estimates:

    P(L > D)

NORMALIZED estimates:

    P(R > D / b)

Both probabilities are scored against the held-out run's five future restores.

Metric:

    Brier score

at:

    10 / 25 / 50 / 100 ms

## Cross-run dispersion

Also compare the run-to-run dispersion of:

    median future latency

against:

    median future residual multiplier

in log space.

If baseline normalization is useful, the latter should collapse much of the
run-level regime variation without erasing the residual tail.

## Important non-goal

Normalization is not expected to make restore latency deterministic.

A successful result should still preserve a material residual tail.

That tail is exactly what the separate tail prior is for.

## North-Star consequence

The Governor state can become:

    tiny current-run baseline
      *
    durable residual-tail prior

rather than keeping a large raw cross-run latency surface resident.

That is a smaller sufficient state for deadline-risk decisions.

## Claim ceiling

**LEAVE_ONE_RUN_OUT_RESIDUAL_TAIL_MODEL_ON_FIFTEEN_REUSED_8MIB_COLD_RUNS_ONLY**
