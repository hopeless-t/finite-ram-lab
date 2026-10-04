# FR-FP-023 Receipt

Status: **PASS / BASELINE-NORMALIZED RESIDUAL TAIL PRIOR QUALIFIED**

Parent: **FR-FP-022**

- workflow run: 37191658436
- job: 111404934891
- execution head: 1e7aa51752a44f13d2a3c43e7752ced26ee5cba8
- reused hosted runs: 15
- future samples: 75
- state size: 8 MiB
- new physical runs: 0

Factorization:

    restore latency = current-run baseline * residual multiplier

Baseline:
- first current-run COLD restore

Residual:
- future restore / first restore

Cross-run dispersion:
- raw future-median log stdev: 1.11775
- normalized future-median log stdev: 0.45478
- reduction: 59.31%

Residual multiplier prior:
- p50: 1.0015x
- p75: 1.2819x
- p90: 5.8547x
- p95: 7.4202x
- max: 7.8030x
- >2x rate: 20.0%
- >5x rate: 13.33%

Leave-one-run-out absolute deadline Brier improvement:

- 10 ms: 53.24%
- 25 ms: 57.32%
- 50 ms: 88.02%
- 100 ms: 37.94%

Normalization improves every tested deadline Brier score while preserving a
material residual tail.

Decision:

**MODEL_COLD_RESTORE_AS_CURRENT_RUN_BASELINE_TIMES_A_RESIDUAL_MULTIPLIER_TAIL_PRIOR**

Governor consequence:

    baseline state:
      CURRENT_RUN_ONE_PROBE

    tail state:
      CROSS_RUN_RESIDUAL_MULTIPLIER_PRIOR

    deadline risk:
      P(residual > deadline / current baseline)

This is a smaller and better calibrated sufficient state than one raw universal
cross-run latency prior.

Claim ceiling:

**LEAVE_ONE_RUN_OUT_RESIDUAL_TAIL_MODEL_ON_FIFTEEN_REUSED_8MIB_COLD_RUNS_ONLY**
