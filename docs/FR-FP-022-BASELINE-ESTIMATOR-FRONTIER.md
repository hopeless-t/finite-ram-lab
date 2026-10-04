# FR-FP-022 — Robust baseline-estimator frontier

Status: **REUSED EVIDENCE ESTIMATOR CANDIDATE**

Parent: **FR-FP-021**

## Why

FR-FP-021 showed that a few current-run restores can calibrate the run-level
baseline, but it also showed that more probes are not automatically safer.

Some hosted runs contain isolated positive latency spikes.

A small-sample median can accidentally promote those spikes into the estimated
baseline.

FR-FP-022 therefore optimizes the estimator as well as the probe count.

## Fair target

Every candidate predicts the same target:

    median(last three 8 MiB COLD restores)

The first 0 / 1 / 2 / 3 restores are available for calibration.

Using one fixed future target avoids making a two-probe estimator look different
simply because its held-out future window changed.

## Candidates

- zero-probe leave-one-run-out prior;
- one-probe first observation;
- two-probe median / minimum / geometric mean;
- three-probe median / minimum / geometric mean.

Metrics:

- mean absolute log error;
- median absolute log error;
- p90 absolute log error;
- maximum absolute log error;
- >25 ms baseline-regime classification errors;
- p50 and maximum calibration cost.

## Expected structure

If slow observations behave as upward tail contamination around a lower run
baseline, the lower envelope may estimate baseline more robustly than a median
at very small k.

This is a candidate interpretation, not a universal latency model.

## No hidden common utility

Memory/latency policy still has no universal scalar utility.

The experiment therefore exposes a Pareto frontier instead of declaring one
probe count universally optimal.

## Governor direction

The intended routing question is:

- need the cheapest current-run regime signal?
  - one probe.
- willing to pay one extra restore for slightly better baseline precision?
  - test two-probe lower envelope.
- assume three probes must be better?
  - no; reject that monotonic assumption on current evidence.

Tail risk remains separate from baseline calibration.

## Claim ceiling

**ESTIMATOR_FRONTIER_ON_FIFTEEN_REUSED_8MIB_COLD_RESTORE_RUNS_ONLY**
