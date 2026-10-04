# FR-FP-024 — Post-training validation of residual-tail priors

Status: **POST-TRAINING VALIDATION CANDIDATE**

Parent: **FR-FP-023**

## Why

FR-FP-023 showed strong leave-one-run-out gains from:

    current-run baseline
      x
    residual multiplier prior

But that result was still evaluated inside the fifteen-run source dataset.

The repository has since generated additional physical FR-FP-016 probes as a
side effect of ordinary downstream CI.

FR-FP-024 uses those later runs without scheduling new runner work.

## Validation set

Selection rules:

- run id later than the FR-FP-020 training cutoff;
- one run per unique commit head;
- complete FR-FP-016 8 MiB COLD trace;
- not present in the original fifteen-run training dataset.

Eight runs qualify in the frozen v0.1 set.

## Competing baseline choices

### ONE_PROBE_FIRST

Baseline:

    first COLD restore

Future:

    remaining five restores

This is the exact factorization used by FR-FP-023.

### TWO_PROBE_MIN

Baseline:

    min(first two COLD restores)

Future:

    remaining four restores

This imports the robust lower-envelope candidate discovered independently by
FR-FP-022.

## Training remains frozen

For each model, the raw latency prior and residual multiplier prior are built
only from the original fifteen training runs.

The eight validation runs never modify those priors.

## What counts as a useful repair

The one-probe model is allowed to fail validation.

That is not a CI failure if the failure is correctly detected and frozen.

The qualification asks whether:

- the one-probe model loses its universal all-deadline advantage;
- the two-probe minimum repairs the observed weakness;
- the residual-tail factorization itself remains useful.

## Self-improvement consequence

This lane tests whether a later research result can repair an earlier model on
evidence that neither result used during its original fit.

That is a stronger closed-loop criterion than repeatedly improving in-sample
scores.

## Claim ceiling

**EIGHT_POST_TRAINING_UNIQUE_HEAD_GITHUB_HOSTED_CI_RUNS_ONLY**
