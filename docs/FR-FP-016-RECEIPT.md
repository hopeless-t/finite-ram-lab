# FR-FP-016 Receipt

Status: **PASS / NEGATIVE RESULT — COLD RESTORE IS NOT ONE STATIONARY SIZE LAW**

Parent: **FR-FP-015**

Three hosted physical runs:

1. workflow 37145768871
2. workflow 37145960094
3. workflow 37146222409

All runs preserved:
- WARM pre-restore file residency;
- COLD DONTNEED nonresidency;
- exact restored bytes / sentinel integrity;
- COLD slower than WARM at 4 / 8 / 16 MiB.

## Run 1

WARM fit R2:
- 0.987

COLD fit R2:
- 0.914

COLD medians:
- 4 MiB: 3.406 ms
- 8 MiB: 4.750 ms
- 16 MiB: 36.574 ms

This suggested an 8->16 MiB knee.

## Run 2

WARM fit R2:
- 0.999

COLD fit R2:
- 0.730

COLD medians:
- 4 MiB: 27.695 ms
- 8 MiB: 140.907 ms
- 16 MiB: 165.444 ms

COLD within-size coefficients of variation:
- 4 MiB: 1.08
- 8 MiB: 0.77
- 16 MiB: 0.61

The first-run knee did not replicate.

## Run 3

WARM fit R2:
- 0.999996

COLD fit R2:
- 0.999951

COLD medians:
- 4 MiB: 43.486 ms
- 8 MiB: 87.643 ms
- 16 MiB: 178.503 ms

COLD single-run effective slope:
- about 11.27 ms/MiB
- about 88.8 MiB/s effective read-bandwidth equivalent

Thus COLD became nearly perfectly linear in run 3, but in a completely different
latency regime.

## Cross-run nonstationarity

8 MiB COLD median:
- 4.750 ms
- 140.907 ms
- 87.643 ms
- max/min ratio: about 29.7x

8 MiB WARM median:
- 0.557 ms
- 1.404 ms
- 0.654 ms
- max/min ratio: about 2.5x

## Theory update

Reject:
- one universal COLD bandwidth;
- one stable 16 MiB restore knee;
- one median restore penalty reused across runs.

Retain:
- WARM is comparatively regular;
- COLD residency is physically distinct;
- COLD restore is consistently slower in these runs;
- COLD latency can be strongly governed by latent run-level I/O state.

The next model must treat COLD restore as a distribution with temporal and
run-level structure.

Decision:

**REJECT_SINGLE_STATIONARY_COLD_RESTORE_SIZE_MODEL_AND_MEASURE_COLD_LATENCY_AS_A_DISTRIBUTION_WITH_TEMPORAL_STRUCTURE**

Next:

Hold state size at 8 MiB and collect a longer paired restore trace with tail
quantiles, deadline-miss rates, burst structure and lag statistics.

Claim ceiling:

**HOSTED_COLD_RESTORE_NONSTATIONARITY_NEGATIVE_RESULT_ONLY**
