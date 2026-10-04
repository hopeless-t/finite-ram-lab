# FR-FP-043 Receipt

Status: **PASS / HOSTED PHYSICAL MIXED HOLD-MIGRATE HYSTERESIS QUALIFIED**

Parent: **FR-FP-042**

Final qualification:
- workflow run: 37214108612
- job: 111471016166
- execution head: 6532642fcb2bec6802c66e583eff9cef7d17441c
- validity horizon: 100 rounds
- state count: 10
- state size: 8 MiB
- WARM slots: 5 = 40 MiB

Qualified hysteresis sequence:

    phase 1 -> 2: MIGRATE
    phase 2 -> 3: MIGRATE
    phase 3 -> 4: HOLD
    phase 4 -> 5: HOLD

All decisions remain deadline-safe.

## Immediate semantic optimum

- physical actions: 24
- service cost: 3090.839 ms
- observed actuation: 555.516 ms
- transparent hybrid total: 3646.355 ms

## Hysteretic physical policy

- physical actions: 16
- service cost: 3137.751 ms
- observed actuation: 400.570 ms
- transparent hybrid total: 3538.321 ms

Difference:

- semantic service cost is 46.912 ms worse under hysteresis;
- observed migration/actuation cost is 154.946 ms lower;
- total is therefore about 108.034 ms lower.

Every phase in both arms:
- resident capacity = exactly 40 MiB;
- WARM states are resident;
- COLD states are nonresident.

Decision:

**PHYSICALLY_MIGRATE_ONLY_WHEN_CROSS_VALIDATED_MIGRATION_COST_CAN_BE_AMORTIZED_WITHIN_THE_EXPECTED_VALIDITY_HORIZON**

Theory update:

The immediate semantic optimum is not necessarily the physical control optimum.

A deliberately retained, slightly worse semantic placement can reduce total
physical cost when the expected validity horizon is too short to amortize the
migration.

Next:

Replace the oracle validity horizon with a decision-directed horizon interval
and stop collecting horizon evidence once the interval lies entirely on one
side of the break-even horizon.

Claim ceiling:

**HOSTED_PHYSICAL_HYSTERESIS_ON_ONE_FIVE_PHASE_EQUAL_SIZE_FIXED_CAPACITY_H100_FIXTURE_ONLY**
