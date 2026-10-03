# FR-FP-016 CI Contract Biopsy — Negative Result Retained as Positive Gate

Status: **META-FAILURE / TEST CONTRACT UPDATED**

Downstream exposure:
- workflow: 37152968895
- branch: research/fr-fp-018-order-null
- unrelated FR-FP-018 analysis itself: PASS
- suite failure source: FR-FP-016

Observed current hosted medians:
- COLD 4 MiB: about 11.45 ms
- COLD 8 MiB: about 3.47 ms
- COLD 16 MiB: about 35.74 ms

The old FR-FP-016 gate required:

    cold_latency_increases_with_size = true

That condition failed.

## Why the test was wrong

FR-FP-016's qualified theory update already rejected:

- one stationary COLD restore bandwidth;
- one stable size knee;
- one reusable per-size median law.

A downstream test should therefore not require one particular monotonic shape
from every future hosted run.

The test suite accidentally retained the hypothesis that the research result
had already rejected.

## Repair

Move current-run COLD size monotonicity from:

    PASS/FAIL scientific gate

to:

    observation telemetry

Retain stable gates:

- exact restore integrity;
- WARM residency;
- COLD nonresidency;
- COLD slower than WARM at every tested size;
- comparatively regular WARM scaling;
- frozen cross-run evidence that the COLD stationary law and fixed knee failed.

## Compiled lesson

**NEGATIVE_RESULT_MUST_REMOVE_THE_REJECTED_SHAPE_FROM_FUTURE_PASS_GATES**

A failure biopsy is incomplete if the theory document changes but executable
qualification continues to enforce the rejected theory.

Claim ceiling:

**TEST_CONTRACT_META_FAILURE_ONLY**
