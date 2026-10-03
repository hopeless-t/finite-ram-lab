# FR-FP-020 Receipt

Status: **PASS / REUSED HOSTED CI CROSS-RUN RESTORE PRIOR QUALIFIED**

Parent: **FR-FP-019**

- workflow run: 37153859007
- job: 111293083296
- execution head: 0ea711294fa04dc921335e4addefa14d69bfc4ce
- new physical runs scheduled by this lane: 0
- reused independent hosted CI runs: 15
- state size: 8 MiB
- bootstrap replicates: 20,000

All source runs preserved:
- exact restore integrity
- WARM pre-residency
- COLD DONTNEED nonresidency
- COLD slower than WARM at every tested size

## Cross-run COLD distribution

8 MiB COLD run medians:
- min: 3.435 ms
- p25: 3.644 ms
- p50: 9.682 ms
- p75: 11.172 ms
- p90: 87.643 ms
- p95/max: 124.148 ms
- mean: 20.425 ms
- CV: 1.741
- max/min: 36.14x
- log-scale standard deviation: 1.119

Empirical run-level deadline-miss rates:
- >5 ms: 60.0%
- >10 ms: 46.7%
- >25 ms: 13.3%
- >50 ms: 13.3%
- >100 ms: 6.7%

20,000-bootstrap 95% intervals:
- median: 3.644 .. 11.172 ms
- P(run median >10 ms): 0.20 .. 0.733
- P(run median >25 ms): 0.00 .. 0.333
- P(run median >50 ms): 0.00 .. 0.333
- P(run median >100 ms): 0.00 .. 0.20

## WARM control

8 MiB WARM run medians:
- min: 0.286 ms
- p50: 0.670 ms
- p90: 1.205 ms
- p95/max: 1.880 ms
- CV: 0.527
- max/min: 6.57x
- log-scale standard deviation: 0.486

COLD run-level log dispersion is therefore materially larger than WARM.

## High-latency regime candidate

Largest adjacent gap in sorted log COLD medians:
- lower edge: 13.157 ms
- upper edge: 87.643 ms
- ratio: 6.661x
- geometric midpoint: 33.958 ms
- runs above the gap: 2 / 15

This is retained as a **candidate** high-latency regime only.

Fifteen runs are not enough to declare a stable discrete mixture model.

Decision:

**MODEL_COLD_RESTORE_WITH_A_RUN_LEVEL_UNCERTAINTY_PRIOR_NOT_A_SINGLE_POINT_LATENCY**

Governor direction:
- reject one universal restore-time point estimate as the sole input;
- carry an empirical run-level prior;
- carry deadline-miss probability with uncertainty;
- update the prior with current-run calibration evidence when available.

Claim ceiling:

**FIFTEEN_REUSED_GITHUB_HOSTED_CI_RUNS_FOR_8MIB_RESTORE_ONLY**
