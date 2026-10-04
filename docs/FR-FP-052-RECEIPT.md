# FR-FP-052 Receipt

Status: **PASS / HOSTED PHYSICAL ONLINE JOINT VARIABLE-SIZE PATH QUALIFIED**

Parent: **FR-FP-051**

Qualification:
- workflow run: 37223002770
- job: 111496933436
- execution head: ef2663a2cf415feb7e0a5e212cda3e29647a10b1
- state sizes MiB: 4 / 6 / 8 / 10 / 12 / 14 / 16 / 8 / 8 / 12
- capacity schedule MiB: 40 / 28 / 72 / 44 / 56

## JOINT path

- service cost: 556.770 ms
- hosted physical actuation: 89.875 ms
- physical hybrid total: 646.645 ms
- physical actions: 8
- prefetch bytes: 52 MiB

Transitions:
- phase 1->2: evict 12 MiB, 11.140 ms
- phase 2->3: promote 40 MiB, 44.455 ms
- phase 3->4: evict 24 MiB, 21.892 ms
- phase 4->5: promote 12 MiB, 12.388 ms

## Migration-blind semantic tracking

- service cost: 538.929 ms
- hosted physical actuation: 172.976 ms
- physical hybrid total: 711.904 ms
- physical actions: 16
- prefetch bytes: 92 MiB

Transitions:
- phase 1->2: +16 MiB / -28 MiB, 51.631 ms
- phase 2->3: +54 MiB / -10 MiB, 66.754 ms
- phase 3->4: +10 MiB / -38 MiB, 43.576 ms
- phase 4->5: +12 MiB, 11.015 ms

## Physical result

JOINT beats migration-blind semantic tracking by:

    65.259 ms

while using:
- 50% fewer tier actions
- ~43.5% fewer promoted bytes

Every phase physically matches its target resident bytes, WARM residency and
COLD nonresidency.

## Model-calibration observation

The FR-FP-048 migration model selected the correct winning path, but the shadow
margin was larger:

- shadow JOINT: 689.685 ms
- shadow semantic: 791.960 ms
- shadow margin: 102.275 ms

Hosted physical margin:
- 65.259 ms

The current hosted run therefore exposes material migration-cost calibration
error without reversing the policy winner.

Decision:

**PHYSICALLY_FOLLOW_THE_JOINT_SERVICE_PLUS_MIGRATION_OPTIMUM_INSTEAD_OF_MIGRATION_BLIND_SEMANTIC_TRACKING**

Next:

Use these held-out physical transitions as current-run migration evidence.
Update or retrain the migration model only if a calibrated model would change
the admissible placement decision.

Claim ceiling:

**HOSTED_PHYSICAL_FIVE_PHASE_VARIABLE_SIZE_JOINT_PATH_ON_ONE_FROZEN_ONLINE_TRACE_ONLY**
