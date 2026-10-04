# FR-FP-049 Receipt

Status: **PASS / JOINT MIGRATION-AWARE BYTE-BUDGET KNAPSACK QUALIFIED**

Parent: **FR-FP-048**

Final qualification:
- workflow run: 37219470496
- job: 111486699274
- execution head: 796ce074070db7f98376a11c195f7c834c93d9c5
- new physical runs: 0
- comparison contexts: 35
- DP vs exhaustive mismatches: 0

Frozen directional migration model from FR-FP-048:

    PROMOTE(ms) = 2.282833 + 1.730256 * MiB
    EVICT(ms)   = 10.115819 + 0.032783 * MiB

Joint objective:

    J(S)
      =
    H * ColdPenalty(S)
      + MigrationCost(S_current -> S)

under:
- target byte budget;
- mandatory WARM deadline guards.

Classification counts:
- HOLD: 12
- SEMANTIC_OPTIMUM: 8
- THIRD_PLACEMENT: 15

Thus the old two-candidate policy:

    HOLD
    or
    migrate to instantaneous semantic optimum

is not complete on this fixture.

Representative third placement:

56 -> 72 MiB, H=50:
- current WARM: {0,1,2,3,7,8,9}
- semantic optimum: {0,1,2,4,5,7,8,9}
- joint optimum: {0,1,2,3,6,7,8,9}

Predicted totals:
- HOLD: 219.462 ms
- semantic optimum: 196.737 ms
- joint: 167.359 ms

The joint solution promotes only state 6 (16 MiB), avoiding the larger
multi-state migration required by the semantic optimum.

Another representative:

28 -> 40 MiB, H=20:
- current: {7,8,9}
- semantic: {0,2,7,8,9}
- joint: {4,7,8,9}

The joint placement promotes one 12 MiB state rather than two smaller states.

Decision:

**OPTIMIZE_SERVICE_AND_MIGRATION_COST_JOINTLY_INSTEAD_OF_LIMITING_CONTROL_TO_HOLD_VS_SEMANTIC_OPTIMUM**

Next:

Physically actuate representative third placements and compare observed
migration cost plus frozen service cost against HOLD and semantic-optimum
controls.

Claim ceiling:

**SYNTHETIC_JOINT_PLACEMENT_USING_FP046_VALUES_FP047_TRANSITIONS_AND_FP048_COST_MODEL_ONLY**
