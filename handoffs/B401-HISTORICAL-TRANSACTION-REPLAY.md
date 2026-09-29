# B401 — Historical transactional replay

## Status

COMPLETE / NO NEW PHYSICAL RUN.

## Objective

Apply the B400 transactional validator to historical Q64 evidence without rewriting frozen experimental endpoints.

## Outputs

- `analysis/inputs/HISTORICAL-TRANSACTION-REPLAY-v1.json`
- `docs/RETROSPECTIVE-TRANSACTIONAL-RECLASSIFICATION-v1.md`

## Main result

The old binary SUCCESS/FAIL population decomposes into:

- pre-transaction predictor hit/miss;
- normalization/recovery;
- verified reset;
- observer/state invalidation;
- receipt-limited NO_RESULT;
- target match/mismatch;
- commit.

### Controlled-spawn v2

Frozen history remains:

- strict success 49/72;
- strict failure 23/72;
- primer found 55/72;
- primer-qualified target pattern 55/55.

B400 replay:

- TX_SUCCESS = 0;
- TX_TARGET_FAIL = 0;
- TX_NO_RESULT_RECEIPT_GAP = 72.

Reason:

controlled-spawn v2 predates the required direct charge-side reset token:

`page_counter_try_charge(64) + refill_stock(63)`.

The zero accepted-success count is therefore a historical certification gap, not a mechanism-performance estimate.

The six historical BAIT_NONZERO failures all retained the predicted terminal phase and are not target failures. The three -17 bait cases are release-compatible after OBS-005, but cannot be retroactively promoted because controlled-spawn lacks the source-grounded per-touch release receipt. The -13/-3/-2 cases remain unknown emissions and fail closed.

The 17 calibration OTHER failures terminated before a verified reset. Under the new architecture a positively classified release-only emission would permit continued normalization, but the historical trace cannot prove the counterfactual outcome.

### OBS-006 corrected

- 14/16 -> TX_NONTERMINAL_VERIFIED;
- 2/16 -> TX_NO_RESULT_INVALIDATED / unexpected refill;
- 0 -> TX_TARGET_FAIL.

OBS-006 is the first historical evidence set that satisfies the direct B400 reset token.

It has no target+commit phase, so it does not become TX_SUCCESS.

### G0 PTE-growth subset

Five LOW specimens were historically Q64 by net memory.current but also had VmPTE growth.

B400 replay:

- 5/5 -> TX_NO_RESULT_INVALIDATED / PTE_GROWTH.

This is an explicit demonstration that the new validator is stricter on the historical success side as well as more informative on the failure side.

### MEMCG-005F / G-A

MEMCG-005F:

- 121 first-touch Q64 -> predictor hit;
- 2 first-touch zero -> normalize needed;
- 0 target failures.

G-A:

- 28 first-touch zero;
- 28/28 later Q64 by touch65;
- replay class = pre-transaction recovery;
- 0 target failures.

Natural first-touch exact-zero incidence remains a hidden-initial-state/predictor estimand rather than a target-failure estimand.

## Frozen-endpoint rule

No historical endpoint was rewritten.

The replay adds a second classification layer rather than replacing the original labels.

## Scientific consequence

There is currently no historical observation of a genuine target mismatch after a B400-complete verified uninterrupted epoch.

This does not establish that the true target-failure probability is zero.

It establishes that the old experiments mixed state acquisition, observation validity, and target execution into a coarser endpoint.

## Stop

PHYSICAL PAUSE.

Next:

design a native controlled-spawn transaction packet bridge so a small future pilot can emit the complete B400 receipt chain from the start.

Do not launch a large reliability panel yet.
