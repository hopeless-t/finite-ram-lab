# FR-FP-042 Receipt

Status: **PASS / CROSS-VALIDATED MIGRATION-COST HYSTERESIS QUALIFIED**

Parent: **FR-FP-041**

- workflow run: 37213805577
- job: 111470139340
- execution head: f6b3e0d93bf0e806f55add47e33bb10e5a5481e8
- new physical runs: 0
- phase horizon: 20 rounds

## Independent physical cost calibration

Calibration source:
- FR-FP-037 / workflow 37205520749
- pure promotion / pure eviction transitions only

Conservative unit costs:
- promote: 15.297145 ms/state
- evict: 10.765429 ms/state

Predicted 4-promote + 4-evict swap:

    104.250296 ms

## Held-out validation

Validation source:
- FR-FP-039 / workflow 37210203932

Observed mixed swaps:
- 99.915626 ms
- 107.480568 ms
- 102.495132 ms

Absolute relative errors:
- 4.34%
- 3.01%
- 1.71%

Maximum:
- 4.34% < 5%

The mixed swaps were not used to fit the model.

## Immediate optimum vs hysteretic placement

Immediate semantic optimum:
- service cost over five 20-round phases: 618.168 ms
- observed migration cost: 309.891 ms
- observed total: 928.059 ms
- model migration cost: 312.751 ms
- model total: 930.919 ms

Hysteretic policy:
- keeps initial placement for all five phases
- semantic service cost: 662.006 ms
- migration cost: 0
- total: 662.006 ms

Thus the hysteretic policy accepts a slightly worse semantic placement but
produces a materially lower physical total on the frozen 20-round horizon.

Decision:

**RETAIN_CURRENT_PLACEMENT_WHEN_EXPECTED_HORIZON_BENEFIT_DOES_NOT_AMORTIZE_A_CROSS_VALIDATED_PHYSICAL_MIGRATION_COST**

Safety boundary:

Hysteresis is bypassed if the retained placement violates the deadline guard.

Theory update:

A slightly worse semantic placement can be the better physical control policy.

Migration hysteresis should be driven by:

    expected benefit per round
    x expected placement-validity horizon

versus:

    independently calibrated physical migration cost

not by an arbitrary score epsilon.

Next:

Use a longer 100-round validity horizon where the same trace contains both
MIGRATE and HOLD decisions, and physically actuate the hysteretic policy.

Claim ceiling:

**CROSS_VALIDATED_COST_MODEL_AND_HYSTERESIS_ON_FP037_038_039_EQUAL_SIZE_FIXED_CAPACITY_EVIDENCE_ONLY**
