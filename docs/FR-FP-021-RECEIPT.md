# FR-FP-021 Receipt

Status: **PASS / FEW-SHOT CURRENT-RUN RESTORE CALIBRATION QUALIFIED**

Parent: **FR-FP-020**

Final qualification:
- workflow run: 37191087246
- job: 111403220648
- execution head: 294a0160dc38cbbbf985cbcd0c93794389bde039
- reused hosted runs: 15
- 8 MiB COLD trials per run: 6
- new physical runs scheduled: 0

Key result:

1 probe:
- mean absolute log error reduction vs leave-one-run-out prior: 79.25%
- future baseline >25 ms classification: 15/15 correct
- p50 calibration cost: 4.439 ms
- max calibration cost: 127.561 ms

3 probes:
- mean absolute log error reduction vs leave-one-run-out prior: 82.18%
- future baseline >25 ms classification: 15/15 correct
- p50 calibration cost: 33.618 ms
- max calibration cost: 386.406 ms

But baseline calibration does not eliminate residual tail risk:
- 3-probe baseline classifier still misses future isolated >25 ms tail events.

Decision:

**SEPARATE_FEW_SHOT_RUN_BASELINE_CALIBRATION_FROM_RESIDUAL_WITHIN_RUN_TAIL_RISK**

Governor consequence:
- calibrate current-run baseline from early restores;
- retain a separate deadline-miss / tail-risk prior;
- do not treat more probes as automatically better;
- do not promote 3 probes as a universal default.

Claim ceiling:

**FIFTEEN_REUSED_RUNS_SIX_TRIALS_EACH_FOR_8MIB_FEW_SHOT_CALIBRATION_ONLY**
