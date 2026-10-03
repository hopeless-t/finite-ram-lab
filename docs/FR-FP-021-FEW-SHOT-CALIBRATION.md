# FR-FP-021 — Few-shot current-run restore calibration

Status: **REUSED EVIDENCE CALIBRATION CANDIDATE**

Parent: **FR-FP-020**

## Question

FR-FP-020 established that the cross-run COLD restore prior is very wide.

A Governor cannot know which hosted I/O regime the current run inhabits from the
global prior alone.

FR-FP-021 asks whether the first few current-run restores can cheaply calibrate
the run-level baseline.

## Frozen evidence

Fifteen existing hosted runs.

Each run has six ordered physical 8 MiB COLD restore trials.

No new runner is scheduled.

For each run and each probe count k in:

    1, 2, 3

use:

    first k trials = calibration evidence
    remaining trials = held-out future

Prediction:

    median(first k)

Future baseline target:

    median(remaining trials)

The comparison prior is leave-one-run-out:

    median(full-run medians from the other fourteen runs)

Thus the current run's future trials do not enter its prior estimate.

## Error metric

Use absolute log error.

This treats multiplicative error symmetrically and matches the observed
multi-order restore range better than raw millisecond error.

## Operational 25 ms split

Also ask two different questions.

### Baseline regime

Does the future median exceed 25 ms?

This captures a persistently high-latency current-run regime.

### Tail event

Does any held-out future restore exceed 25 ms?

This captures isolated slow events.

They are deliberately not the same target.

## Expected theory shape

Early calibration may identify the run baseline well.

It may still fail to predict isolated future spikes.

If so the Governor should maintain two uncertainty layers:

    current-run baseline calibration

plus:

    residual within-run tail prior

rather than replacing the broad prior with one calibrated point estimate.

## Probe cost

The actual milliseconds consumed by the calibration restores are preserved.

A later lane may optimize probe count against value-of-information and startup
latency.

This PR does not declare three probes a universal default.

## Claim ceiling

**FIFTEEN_REUSED_RUNS_SIX_TRIALS_EACH_FOR_8MIB_FEW_SHOT_CALIBRATION_ONLY**
