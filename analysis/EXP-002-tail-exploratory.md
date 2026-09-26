# EXP-002 Tail Exploration

> **Status:** EXPLORATORY / NOT A FINDING  
> **Source run:** 36228994342

## Purpose

EXP-002 did not pre-register a tail-risk endpoint.

This document therefore uses the already-collected EXP-002 trials only to generate a new, independently testable hypothesis.

No p-value or confidence interval in a future tail study may be back-projected onto this exploratory dataset.

## HOT-retouch distribution

| Arm | N | P50 ms | P75 ms | P90 ms | P95 ms | P99 ms | Max ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CORRECT_PAGEOUT | 120 | 0.518 | 8.463 | 76.713 | 286.499 | 459.904 | 677.849 |
| NO_HINT | 120 | 0.686 | 2.221 | 137.958 | 442.030 | 1473.385 | 2109.574 |
| WRONG_PAGEOUT | 120 | 54.396 | 85.525 | 279.677 | 843.137 | 1146.387 | 1547.876 |

## Threshold exploration

| Arm | >=10 ms | >=25 ms | >=50 ms | >=100 ms | >=250 ms | >=500 ms | >=1000 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CORRECT_PAGEOUT | 30/120 | 27/120 | 21/120 | 10/120 | 8/120 | 1/120 | 0/120 |
| NO_HINT | 28/120 | 20/120 | 17/120 | 14/120 | 8/120 | 6/120 | 5/120 |
| WRONG_PAGEOUT | 120/120 | 108/120 | 74/120 | 26/120 | 14/120 | 8/120 | 4/120 |

Runner blocks containing at least one event:

| Arm | >=100 ms | >=250 ms | >=500 ms | >=1000 ms |
| --- | ---: | ---: | ---: | ---: |
| CORRECT_PAGEOUT | 7/20 | 6/20 | 1/20 | 0/20 |
| NO_HINT | 6/20 | 5/20 | 4/20 | 4/20 |
| WRONG_PAGEOUT | 10/20 | 5/20 | 4/20 | 3/20 |

## Important non-result

CORRECT_PAGEOUT did **not** uniformly reduce slow-event incidence.

At 10, 25, and 50 ms thresholds, CORRECT_PAGEOUT had as many or more events than NO_HINT.

The exploratory difference appears only in the far extreme tail:

    >=500 ms:
      CORRECT_PAGEOUT  1 / 120  (0.83%)
      NO_HINT          6 / 120  (5.00%)

    >=1000 ms:
      CORRECT_PAGEOUT  0 / 120
      NO_HINT          5 / 120  (4.17%)

Therefore the new hypothesis should be about **catastrophic-tail risk**, not general latency reduction.

## Candidate independent hypothesis

> Under the same 164 MiB natural-pressure workload, correctly PAGEOUT-preparing the not-soon-needed region reduces the probability of a catastrophic HOT-retouch stall of at least 500 ms relative to NO_HINT.

## Why 500 ms is a defensible candidate threshold

The 500 ms scale is not invented solely from this table:

- OBS-001 originally observed a HOTSET_RETOUCH event around 486.7 ms;
- CHAR-001's pressured regime was commonly around 0.8–1.0 s;
- EXP-002 exploration shows separation mainly above this scale.

Nevertheless, because EXP-002 was inspected first, 500 ms must be treated as a **new pre-registered endpoint for independent data**.

## Design implication

The exploratory rates are sparse and clustered by runner.

A new study needs substantially more repeated trials and independent runner blocks than a central-tendency comparison.

Do not reuse EXP-002 observations as confirmatory samples.
