# FR-FP-024 Receipt

Status: **PASS / POST-TRAINING UNIQUE-HEAD VALIDATION QUALIFIED**

Parent: **FR-FP-023**

- workflow run: 37192027517
- job: 111406064720
- execution head: 773182e8184fe822ef0d2bf8456b0534a6360521
- frozen training runs: 15
- post-training validation runs: 8 unique commit heads
- state size: 8 MiB
- new physical runs scheduled by this lane: 0

## ONE_PROBE_FIRST

Residual-tail factorization retained partial value:

- 10 ms Brier improvement: 34.76%
- 25 ms Brier improvement: **-1.69%**
- 50 ms Brier improvement: 39.08%
- 100 ms Brier improvement: 100%

Thus the FR-FP-023 in-dataset claim that one-probe normalization improves every
tested deadline did **not** externally replicate at 25 ms.

## TWO_PROBE_MIN

Importing the robust lower-envelope baseline from FR-FP-022 repaired the
validation weakness:

- 10 ms Brier improvement: 35.14%
- 25 ms Brier improvement: 5.53%
- 50 ms Brier improvement: 38.34%
- 100 ms Brier improvement: 100%

The normalized model improves every tested deadline on the frozen eight-run
post-training validation set.

## Theory update

Retain:

    restore latency
      =
    current-run baseline
      x
    residual-multiplier tail

Narrow:

    ONE_PROBE_FIRST improves every deadline

to:

    ONE_PROBE_FIRST is a cheap baseline signal but is not sufficiently robust
    for every deadline on post-training validation.

Promote as the stronger validated baseline candidate:

    TWO_PROBE_MIN

Residual tail uncertainty remains separate and must not be collapsed into the
baseline estimate.

Decision:

**RETAIN_RESIDUAL_TAIL_FACTORIZATION_BUT_PROMOTE_TWO_PROBE_MIN_AS_THE_MORE_ROBUST_VALIDATED_BASELINE_FOR_DEADLINE_RISK**

Claim ceiling:

**EIGHT_POST_TRAINING_UNIQUE_HEAD_GITHUB_HOSTED_CI_RUNS_ONLY**
