# FR-FP-033 — Decision-relevance early stop for COLD calibration

Status: **REUSED-EVIDENCE EARLY-STOP CANDIDATE**

Parent: **FR-FP-032**

## Why

FR-FP-032 qualified decision-relevance pruning for the reuse-monitoring plane.

The next question is whether the same principle reproduces in a different
decision plane.

FR-FP-033 tests the physical-calibration measurement plane.

## Baseline contract

The qualified robust baseline candidate is:

    TWO_PROBE_MIN

Therefore the second probe can only:

    keep the first baseline
    or
    lower it

It cannot increase the baseline.

The FR-FP-025/026 reuse ceiling is monotonic in that direction:

    lower baseline
      -> no larger expected COLD penalty
      -> no larger deadline miss probability
      -> reuse ceiling cannot decrease

## Exact early-stop gate

If after probe 1:

    reuse ceiling == 1

then the second probe cannot reduce that ceiling below 1.

The second probe is decision-irrelevant and can be skipped.

If after probe 1:

    reuse ceiling < 1

the second probe remains resident in the measurement plan because a lower second
measurement may change the decision surface.

## Backtest

Use the 15 hosted runs already frozen in the restore dataset.

For each held-out run:

1. build residual and WARM priors from the other 14 runs;
2. calculate the risk surface from the first COLD probe;
3. apply the early-stop gate;
4. compare with the actual TWO_PROBE_MIN surface.

No new physical runner is scheduled.

## Qualification

Require:

- at least one run where the second probe can be skipped;
- zero early-stop cases where the two-probe ceiling falls below 1;
- at least one run where the second probe changes the surface, proving the probe
  is not globally redundant.

## Meta significance

This is an independent decision plane from reuse monitoring.

The candidate tests the same higher-order rule:

> stop measuring once the remaining measurement cannot change an admissible
> decision.

A universal meta-skill is still withheld until this replication qualifies.

## Claim ceiling

**LEAVE_ONE_RUN_OUT_EARLY_STOP_BACKTEST_ON_FIFTEEN_8MIB_HOSTED_RESTORE_RUNS_AND_ONE_POLICY_POINT_ONLY**
