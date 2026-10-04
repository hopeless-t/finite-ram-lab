# FR-FP-051 — Online joint variable-size placement

Status: **SYNTHETIC ONLINE JOINT-OPTIMIZATION CANDIDATE**

Parent: **FR-FP-050**

## Why

FR-FP-050 physically validated that partial third placements can beat both HOLD
and migration-blind semantic optima.

The next step is to return that joint objective to the online Governor.

## Online evidence

Reuse the five FR-FP-038 evidence phases unchanged.

Each phase updates conservative per-state expected COLD penalties.

Project those values onto the qualified heterogeneous state-size vector:

    4,6,8,10,12,14,16,8,8,12 MiB

## Dynamic byte capacity

Frozen schedule:

    40 -> 28 -> 72 -> 44 -> 56 MiB

Phase validity horizon:

    20 rounds

## Old architecture

At each phase:

1. compute a migration-blind semantic optimum;
2. separately decide whether to migrate with a hysteresis gate.

## Candidate architecture

Directly solve:

    min_S
        H * ColdPenalty_t(S)
      + MigrationCost(S_previous -> S)

subject to:

- current byte budget;
- current deadline-mandatory WARM constraints.

No semantic optimum is required as an intermediate control target.

## Exactness

For phases 2..5, compare the joint DP with exhaustive subset search.

Phase 1 starts at the migration-blind semantic optimum because there is no prior
placement to migrate from.

## Comparator

Run a separate migration-blind tracking policy:

- select the semantic optimum every phase;
- pay the same frozen FR-FP-048 migration model between its own consecutive
  placements.

Compare cumulative:

    service + migration

across all five phases.

## Expected qualitative behavior

The candidate does not require every phase to be a third placement.

Some phases may:
- HOLD;
- reach semantic optimum;
- select a third partial migration.

The policy is qualified by exact objective minimization, not by a desired mix of
classifications.

## Claim ceiling

**SYNTHETIC_FIVE_PHASE_VARIABLE_SIZE_DYNAMIC_CAPACITY_JOINT_OPTIMIZATION_USING_REUSED_HOSTED_COST_EVIDENCE_ONLY**
