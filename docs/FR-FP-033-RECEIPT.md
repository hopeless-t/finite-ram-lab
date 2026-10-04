# FR-FP-033 Receipt

Status: **PASS / CALIBRATION DECISION-RELEVANCE EARLY STOP QUALIFIED**

Parent: **FR-FP-032**

- workflow run: 37203947209
- job: 111441134419
- execution head: da728378dd014434eaac453ab9e40e90288b4c59
- reused hosted runs: 15
- new physical runs: 0
- state size: 8 MiB
- policy point:
  - lambda = 1.0 ms/MiB
  - deadline = 25 ms
  - miss tolerance = 5%
- baseline estimator: TWO_PROBE_MIN

Qualified early-stop law:

    if first-probe reuse ceiling == 1:
        stop calibration after one probe

Reason:

TWO_PROBE_MIN can only keep or lower the first-probe baseline.
Lower baseline cannot increase expected COLD penalty or deadline miss risk.
Therefore the reuse ceiling cannot fall below 1 after the second probe.

Backtest:
- early-stop runs: 2 / 15
- full two-probe runs retained: 13 / 15
- unsafe early stops: 0
- runs where the second probe actually changed the decision surface: 4 / 15
- counterfactual second-probe latency saved: 23.969 ms total
- median saved probe latency among early-stop runs: 11.984 ms

Important negative result:

The second probe is not globally redundant.

For example, one held-out run moved from:
- first-probe reuse ceiling 0.9333
to:
- two-probe reuse ceiling 1.0

Therefore:
- do not hardcode ONE_PROBE;
- do not hardcode TWO_PROBE;
- stop only when the remaining measurement is proven decision-irrelevant.

Decision:

**EARLY_STOP_COLD_CALIBRATION_ONLY_WHEN_THE_FIRST_PROBE_ALREADY_MAKES_REUSE_DECISION_IRRELEVANT**

Meta significance:

Decision-relevance pruning now has independent evidence in:
1. reuse-monitoring control plane (FR-FP-032);
2. calibration-measurement plane (FR-FP-033).

This supports testing a cross-plane meta-meta capsule.

Claim ceiling:

**LEAVE_ONE_RUN_OUT_EARLY_STOP_BACKTEST_ON_FIFTEEN_8MIB_HOSTED_RESTORE_RUNS_AND_ONE_POLICY_POINT_ONLY**
