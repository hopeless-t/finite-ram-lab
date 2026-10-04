# FR-FP-042 — Cross-validated migration-cost hysteresis

Status: **REUSED HOSTED PHYSICAL HYSTERESIS CANDIDATE**

Parent: **FR-FP-041**

## Why

FR-FP-041 established that the immediate semantic optimum can lose after
physical migration cost is priced.

FR-FP-042 builds the smallest inspectable migration-cost model and uses it to
gate placement changes.

## Independent cost calibration

Calibrate only on FR-FP-037 pure transitions.

Pure WARM promotions:
- 4-state promotion: 60.901 ms
- 2-state promotion: 30.594 ms

Conservative promote unit cost:

    max observed promote ms/state

Pure COLD evictions:
- 2-state eviction: 21.531 ms
- 3-state eviction: 31.390 ms

Conservative evict unit cost:

    max observed evict ms/state

Prediction:

    migration cost
      =
    promote_count * promote_unit
      +
    evict_count * evict_unit

## Held-out physical validation

Do not fit to FR-FP-039.

Validate the model on its three held-out 4-promote + 4-evict swaps:

- 99.916 ms
- 107.481 ms
- 102.495 ms

Qualification requires maximum relative error <5%.

## Hysteresis

For each new value phase:

    expected benefit over horizon
      =
    (old placement penalty - new optimum penalty)
      * expected validity horizon

Migrate only if:

    expected horizon benefit
      >=
    predicted physical migration cost

unless the retained placement violates the deadline guard.

Safety overrides hysteresis.

## Frozen horizon

Use the actual FR-FP-038 evidence phase length:

    20 rounds

This is not a universal horizon.

It is the first closed-loop test of migration-aware placement.

## Evaluation

Compare:

IMMEDIATE_OPTIMUM
: follow every semantic optimum and pay migration.

HYSTERETIC
: retain the current placement until benefit amortizes migration.

Report service penalty and migration cost separately, plus their total.

The purpose is not to hide both in one unexplained utility. The total is only a
comparison after each component is separately visible.

## Claim ceiling

**CROSS_VALIDATED_COST_MODEL_AND_HYSTERESIS_ON_FP037_038_039_EQUAL_SIZE_FIXED_CAPACITY_EVIDENCE_ONLY**
