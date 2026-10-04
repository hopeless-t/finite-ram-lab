# FR-FP-053 — Current-run migration calibration

Status: **MODEL-MAINTENANCE DECISION-RELEVANCE CANDIDATE**

Parent: **FR-FP-052**

## Why

FR-FP-052 showed:

- the FP048 structural migration model selected the correct winning path;
- but it materially overpredicted migration cost on the current hosted run.

Prediction error alone does not prove that the structural model should be
refitted.

Finite RAM asks a narrower question:

> can a much smaller current-run calibration repair the useful prediction
> surface, and does the placement decision change?

## Calibration evidence

Use only the JOINT path's pure-direction transitions:

- EVICT 12 MiB
- PROMOTE 40 MiB
- EVICT 24 MiB
- PROMOTE 12 MiB

Fit two multiplicative current-run scales on top of the frozen FP048 affine-byte
model:

    promote current-run scale
    evict current-run scale

No affine intercept or slope is structurally refit.

## Holdout

The migration-blind semantic arm is not used for calibration.

Its four mixed PROMOTE+EVICT transitions are a held-out validation set.

Compare:

- frozen FP048 model;
- frozen FP048 model × two current-run direction scales.

## Decision-relevance test

Re-run the complete FP051 five-phase exact optimizer with the scaled migration
cost.

If the optimal WARM path is unchanged, structural model refit is
decision-irrelevant for this trace.

If the path changes, model maintenance becomes relevant and must be escalated.

## Why this is different from ignoring error

The gate requires both:

1. held-out mixed-transition prediction improves;
2. the admissible placement path remains unchanged.

Large prediction error is not hidden.

It is compressed into the smallest calibration state that restores useful
prediction without unnecessary structural retraining.

## Claim ceiling

**CURRENT_RUN_DIRECTION_SCALING_AND_REFIT_SKIP_ON_ONE_FP052_HOSTED_TRACE_ONLY**
