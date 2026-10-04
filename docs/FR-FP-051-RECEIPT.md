# FR-FP-051 Receipt

Status: **PASS / ONLINE JOINT VARIABLE-SIZE PLACEMENT QUALIFIED**

Parent: **FR-FP-050**

Qualification:
- workflow run: 37220346757
- job: 111489239283
- execution head: f9bfa477f53820990d8144d18aad5f78915bda56
- phase count: 5
- state sizes MiB: 4 / 6 / 8 / 10 / 12 / 14 / 16 / 8 / 8 / 12
- capacity schedule MiB: 40 / 28 / 72 / 44 / 56
- phase horizon: 20 rounds

Joint objective:

    H * ColdPenalty(S) + MigrationCost(current -> S)

Validation:
- every joint DP result matches exhaustive search
- every joint placement respects the phase byte budget
- at least one third placement exists
- every joint step beats migration-blind semantic tracking from the same current state

Joint path:
- total service cost: 556.770 ms
- total migration cost: 132.915 ms
- total: 689.685 ms

Migration-blind semantic tracking:
- total service cost: 538.929 ms
- total migration cost: 253.031 ms
- total: 791.960 ms

Net reduction from joint optimization:

    102.275 ms

Classification counts after the initial phase:
- HOLD: 0
- SEMANTIC_OPTIMUM: 2
- THIRD_PLACEMENT: 2

Notable phases:

Phase 2, 40 -> 28 MiB:
- joint WARM: {0,2,7,8}
- semantic WARM: {0,1,2,3}
- joint total: 175.161 ms
- semantic-from-joint-state total: 212.347 ms

Phase 3, 28 -> 72 MiB:
- joint WARM: {0,1,2,3,4,7,8,9}
- semantic WARM: {0,1,2,4,5,7,8,9}
- joint total: 136.633 ms
- semantic-from-joint-state total: 141.532 ms

Decision:

**REOPTIMIZE_ONLINE_STATE_PLACEMENT_DIRECTLY_IN_SERVICE_PLUS_MIGRATION_COST_SPACE**

Theory update:

A separate hysteresis gate over a migration-blind optimum is not required once
migration cost is part of the admissible placement objective itself.

The optimal control action may be:
- HOLD,
- the instantaneous semantic optimum,
- or a third partial-migration placement.

Next:

Physically actuate the five-phase joint path and compare it with
migration-blind semantic tracking on the same hosted variable-size fixture.

Claim ceiling:

**SYNTHETIC_FIVE_PHASE_VARIABLE_SIZE_DYNAMIC_CAPACITY_JOINT_OPTIMIZATION_USING_REUSED_HOSTED_COST_EVIDENCE_ONLY**
