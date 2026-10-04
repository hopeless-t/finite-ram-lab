# FR-FP-049 — Joint migration-aware byte-budget placement

Status: **REUSED-EVIDENCE JOINT-OPTIMIZATION CANDIDATE**

Parent: **FR-FP-048**

## Why

The earlier hysteresis model used two candidates:

    HOLD current placement

or:

    migrate to the instantaneous semantic optimum

That is not generally the complete physical control problem.

With heterogeneous state sizes and byte-dependent migration costs, a third
placement can have lower total cost than both.

## Joint objective

For candidate WARM set S:

    J(S)
      =
    H * ColdPenalty(S)
      + MigrationCost(S_current -> S)

where the migration model is frozen from FR-FP-048.

PROMOTE:

    2.282833
      + 1.730256 * MiB

EVICT:

    10.115819
      + 0.032783 * MiB

The candidate must:
- fit the target byte budget;
- keep all deadline-mandatory WARM states.

## Exact DP

The objective is separable by state.

Each state contributes one of two costs:

WARM
: zero cold-service penalty plus promotion cost when currently COLD.

COLD
: H times expected cold penalty plus eviction cost when currently WARM.

A byte-budget DP minimizes total cost.

For every context, compare the DP against exhaustive subset search.

## Evaluation grid

Use consecutive FR-FP-047 budget transitions:

    28 -> 40 -> 56 -> 72 -> 92 -> 44 MiB

and horizons:

    1 / 5 / 10 / 20 / 50 / 100 / 250 rounds

Total:

    35 contexts

Each result is classified:

HOLD
: joint optimum equals the old placement.

SEMANTIC_OPTIMUM
: joint optimum equals the migration-blind semantic optimum.

THIRD_PLACEMENT
: joint optimum is neither.

The experiment does not require a third placement to exist.

If none exists, the two-candidate hysteresis approximation survives this
fixture.

If one exists, the approximation is disproven.

## Claim ceiling

**SYNTHETIC_JOINT_PLACEMENT_USING_FP046_VALUES_FP047_TRANSITIONS_AND_FP048_COST_MODEL_ONLY**
