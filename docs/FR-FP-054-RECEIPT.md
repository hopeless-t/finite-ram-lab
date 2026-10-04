# FR-FP-054 Receipt

Status: **PASS / ENDOGENOUS RESIDENT-BYTE-TIME FRONTIER QUALIFIED**

Parent: **FR-FP-053**

Qualification:
- workflow run: 37224069602
- job: 111499994465
- execution head: 03a69dfaeb76ee0d08e633fc899e4999e8b1e22a
- new physical runs: 0
- DP vs exhaustive mismatches: 0

Hard capacity schedule remains an external maximum:

    40 / 28 / 72 / 44 / 56 MiB

The exact objective is:

    H * ColdPenalty(S)
      + MigrationCost(current -> S)
      + H * lambda * WarmMiB(S)

where lambda prices resident byte-time.

The Governor is allowed to leave capacity unused.

Selected frontier points:

lambda = 0
- used MiB: 40 / 28 / 68 / 44 / 56
- resident integral: 4720 MiB-round
- service: 556.770 ms
- migration: 89.875 ms

lambda = 0.075
- used MiB: 40 / 28 / 56 / 44 / 44
- resident integral: 4240 MiB-round

lambda = 0.10
- used MiB: 40 / 28 / 34 / 34 / 34
- resident integral: 3400 MiB-round
- service: 726.527 ms
- migration: 18.111 ms

lambda = 0.15
- used MiB: 32 / 26 / 26 / 26 / 26
- resident integral: 2720 MiB-round

lambda = 0.25
- used MiB: 8 / 4 / 4 / 4 / 4
- resident integral: 480 MiB-round

lambda = 0.40
- used MiB: 0 / 0 / 0 / 0 / 0
- resident integral: 0 MiB-round

Across the frozen lambda grid:
- aggregate residency is nonincreasing with memory rent;
- each phase residency is nonincreasing;
- positive rent can deliberately leave hard capacity unused;
- lambda=0 exactly recovers the FR-FP-053 joint path.

Decision:

**TREAT_WARM_CAPACITY_AS_A_HARD_MAXIMUM_AND_CHOOSE_ACTUAL_RESIDENT_BYTES_ENDOGENOUSLY_BY_PRICING_RESIDENT_BYTE_TIME**

North Star:

**MINIMIZE_RESIDENT_BYTE_TIME_WHILE_RETAINING_ONLY_SEMANTIC_VALUE_THAT_JUSTIFIES_ITS_SERVICE_AND_MIGRATION_COST**

Next:

Physically actuate representative low/medium/high rent points and verify that
unused capacity is real hosted page-cache nonresidency rather than a shadow-only
artifact.

Claim ceiling:

**SYNTHETIC_RESIDENT_RENT_FRONTIER_ON_FP051_PHASES_WITH_FP053_CURRENT_RUN_MIGRATION_SCALES_ONLY**
