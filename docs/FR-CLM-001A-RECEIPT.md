# FR-CLM-001A — Synthetic Semantic Working-Set Receipt

Status: **PASS / SYNTHETIC HARNESS VALIDATED**

## Frozen qualification

- workflow run: 36999197789
- job: 110812741798
- execution head: f420d3bd659f7897744992b9a24a25c62273b7ba
- tests: 5/5 PASS
- artifact ID: 11222962121
- artifact ZIP SHA256: e4e7b7a5d4f4111c33263739d5db723e92469fac98d32e88ccc9ef6f91668368
- spec SHA256: 6be2243a3c8609ce5b16128ac308aae9d335a4c925a790425120f3662159d9dc
- result SHA256: 5aa02553bdb08cdffa109c5b7ccf6722a3c6d631aab0ed6129a9d1d28a512274
- corpus SHA256: ccbca20e7a7f476186793fc35c5bc57b5ccdbe243d620673cd94ffdd34235c3a

## Primary result

First budget with exact rate 1.0:

- APPEND_TRUNCATE: **8**
- KEY_AWARE: **2**

At resident budget 2:

- APPEND_TRUNCATE exact rate: **0.25**
- KEY_AWARE exact rate: **1.00**

This is a property of the frozen synthetic corpus and deterministic policies.

It is not a language-model performance result.

## Pressure curve

| policy | budget | exact rate | mean interference |
|---|---:|---:|---:|
| APPEND_TRUNCATE | 1 | 0.25 | 0.75 |
| APPEND_TRUNCATE | 2 | 0.25 | 1.75 |
| APPEND_TRUNCATE | 4 | 0.25 | 3.25 |
| APPEND_TRUNCATE | 6 | 0.50 | 5.00 |
| APPEND_TRUNCATE | 8 | 1.00 | 6.50 |
| KEY_AWARE | 1 | 0.50 | 0.00 |
| KEY_AWARE | 2 | 1.00 | 0.50 |
| KEY_AWARE | 4 | 1.00 | 2.50 |
| KEY_AWARE | 6 | 1.00 | 4.50 |
| KEY_AWARE | 8 | 1.00 | 6.50 |

## What was learned

The harness now distinguishes three quantities that a token-count-only experiment would
collapse:

1. resident representation size;
2. semantic omission / exactness loss;
3. irrelevant resident interference.

The early-single fixture also proves the failure-biopsy path can identify the exact
required key lost by recency truncation.

## Important non-claim

Do **not** interpret the 8-to-2 knee difference as a 4x CLM improvement.

KEY_AWARE is a deterministic synthetic heuristic with explicit query-key access.
No model, provider, learned context manager, Pi harness, or KITten worker was evaluated.

## Research value

FR-CLM-001A validates the measurement apparatus needed for the semantic version of the
Finite RAM principle:

`semantic obligation != simultaneously resident context representation`.

It also confirms that resident-size reduction must always be paired with a semantic gate.

## Next

FR-CLM-001B should add stochastic/rare omission cases and repeated trials so the lab can
exercise:

- rare-event capture;
- failure-state biopsy;
- pressure-knee uncertainty;
- treatment/reference replication;

before moving to a real model-managed context system.

## Claim ceiling

**SYNTHETIC_SEMANTIC_WORKING_SET_HARNESS_ONLY**
