# FR-FP-050 Receipt

Status: **PASS / HOSTED PHYSICAL THIRD-PLACEMENT VALIDATION QUALIFIED**

Parent: **FR-FP-049**

Final qualification:
- workflow run: 37219847273
- job: 111487786221
- execution head: 3a41c9385fa70338fece8fb791a5e92cfdb05ced

Two high-margin FR-FP-049 third-placement contexts were physically actuated on
fresh hosted Linux fixtures.

## Context A — GROWTH 56 -> 72 MiB, H=50

Current:
    {0,1,2,3,7,8,9}

Joint:
    {0,1,2,3,6,7,8,9}

Semantic optimum:
    {0,1,2,4,5,7,8,9}

Observed:
- joint actions: 1
- joint migration: 13.388 ms
- joint service model: 137.392 ms
- joint hybrid total: 150.780 ms
- semantic actions: 3
- semantic migration: 50.413 ms
- semantic service model: 136.741 ms
- semantic hybrid total: 187.154 ms
- HOLD hybrid total: 219.463 ms
- physical resident bytes: exactly 72 MiB

Thus the partial third placement beats both migration-blind semantic optimum and
HOLD.

## Context B — SHRINK 92 -> 44 MiB, H=20

Current placement is infeasible at the new capacity.

Joint:
    {0,4,7,8,9}

Semantic optimum:
    {1,3,7,8,9}

Observed:
- joint actions: 4
- joint migration: 44.710 ms
- joint service model: 115.459 ms
- joint hybrid total: 160.170 ms
- semantic actions: 6
- semantic migration: 64.260 ms
- semantic service model: 114.336 ms
- semantic hybrid total: 178.596 ms
- physical resident bytes: exactly 44 MiB

## Cost-model observation

FR-FP-048 prediction error:
- growth joint 16 MiB promotion: predicted 29.967 ms / observed 13.388 ms
- shrink joint: predicted 42.037 ms / observed 44.710 ms

The byte model is conservative on the growth promotion in this run, yet the
third-placement result remains stronger rather than reversing.

Decision:

**PHYSICALLY_SELECT_PARTIAL_MIGRATION_WHEN_IT_BEATS_BOTH_HOLD_AND_MIGRATION_BLIND_SEMANTIC_OPTIMUM**

Theory update:

Hysteresis should not be implemented as a binary gate over an instantaneous
semantic optimum.

The physically relevant control problem is direct optimization over all
admissible placements with service and migration costs priced jointly.

Claim ceiling:

**HOSTED_PHYSICAL_VALIDATION_OF_TWO_FP049_THIRD_PLACEMENT_CONTEXTS_ONLY**
