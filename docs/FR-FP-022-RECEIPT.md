# FR-FP-022 Receipt

Status: **PASS / ROBUST FEW-SHOT BASELINE ESTIMATOR FRONTIER QUALIFIED**

Parent: **FR-FP-021**

- workflow run: 37191325534
- job: 111403947446
- execution head: 319fbc96a94b49274cf7432d1ad3808ac9fbc44a
- reused hosted runs: 15
- state size: 8 MiB
- new physical runs: 0
- common target: median of the final three COLD restores in every run

Key candidates:

0-probe leave-one-run-out prior:
- mean absolute log error: 0.9858
- p90 absolute log error: 2.4079
- max absolute log error: 2.6751
- >25 ms baseline classification errors: 2
- calibration cost: 0

1-probe first observation:
- mean absolute log error: 0.0970
- median absolute log error: 0.0860
- p90 absolute log error: 0.2389
- max absolute log error: 0.2798
- >25 ms baseline classification errors: 0
- p50 calibration cost: 4.439 ms

2-probe median:
- mean absolute log error: 0.3727
- p90 absolute log error: 1.3977
- max absolute log error: 1.4624
- dominated by 1-probe first observation

2-probe minimum / lower envelope:
- mean absolute log error: 0.0839
- median absolute log error: 0.0613
- p90 absolute log error: 0.2389
- max absolute log error: 0.2798
- >25 ms baseline classification errors: 0
- p50 calibration cost: 22.520 ms

3-probe median:
- median absolute log error: 0.0508
- mean absolute log error: 0.1757
- max absolute log error: 1.8124
- better median but materially worse worst-case than 1-probe

3-probe minimum:
- dominated by 2-probe minimum

Theory update:

More probes are not monotonically better.

Small-k medians can be contaminated by positive latency-tail observations and
promote transient stalls into the run baseline.

The frozen evidence supports:
- one probe as the cheap regime-classification candidate;
- two-probe lower envelope as an optional precision candidate;
- rejection of two-probe median on this evidence;
- rejection of the assumption that three probes must improve the estimate;
- residual tail risk remains separate from baseline calibration.

Decision:

**USE_ONE_PROBE_FOR_CHEAP_REGIME_CLASSIFICATION_AND_CONSIDER_TWO_PROBE_LOWER_ENVELOPE_ONLY_WHEN_EXTRA_BASELINE_PRECISION_JUSTIFIES_THE_COST**

Claim ceiling:

**ESTIMATOR_FRONTIER_ON_FIFTEEN_REUSED_8MIB_COLD_RESTORE_RUNS_ONLY**
