# FR-FP-055 Receipt

Status: **PASS / HOSTED PHYSICAL ENDOGENOUS RESIDENT-BYTE-TIME FRONTIER QUALIFIED**

Parent: **FR-FP-054**

Qualification:
- workflow run: 37224456783
- job: 111501113657
- execution head: 99f772274087e4b6f5aac5c8d14ef0584bfc790c
- four representative memory-rent policy points
- ten heterogeneous states
- five physical phases

Hard capacity remains:

    40 / 28 / 72 / 44 / 56 MiB

## lambda = 0

Physical used MiB:

    40 / 28 / 68 / 44 / 56

- resident integral: 4720 MiB-round
- physical actions: 8
- physical actuation: 92.918 ms
- prefetch: 52 MiB

## lambda = 0.10

Physical used MiB:

    40 / 28 / 34 / 34 / 34

Physical unused MiB:

    0 / 0 / 38 / 10 / 22

- resident integral: 3400 MiB-round
- reduction vs lambda=0: 27.97%
- physical actions: 2
- physical actuation: 20.183 ms
- prefetch: 6 MiB

## lambda = 0.25

Physical used MiB:

    8 / 4 / 4 / 4 / 4

Physical unused MiB:

    32 / 24 / 68 / 40 / 52

- resident integral: 480 MiB-round
- reduction vs lambda=0: 89.83%
- physical actions: 2
- physical actuation: 19.070 ms
- prefetch: 4 MiB

## lambda = 0.40

Physical used MiB:

    0 / 0 / 0 / 0 / 0

Physical unused MiB:

    40 / 28 / 72 / 44 / 56

- resident integral: 0 MiB-round
- reduction vs lambda=0: 100%
- physical actions: 0
- physical actuation: ~0 ms
- prefetch: 0

All target WARM files are physically resident and all target COLD files are
physically nonresident within the frozen thresholds.

Every physical resident integral exactly matches the FR-FP-054 shadow value.

Decision:

**PHYSICALLY_LEAVE_WARM_CAPACITY_UNUSED_WHEN_RESIDENT_BYTE_TIME_COST_EXCEEDS_THE_SEMANTIC_VALUE_IT_SAVES**

North-Star consequence:

The Governor no longer merely decides which states fit.

It can now physically decide how many resident bytes are worth retaining at all.

A hard capacity is a safety ceiling, not a utilization target.

Claim ceiling:

**HOSTED_PHYSICAL_RESIDENT_RENT_ACTUATION_AT_FOUR_POLICY_POINTS_ON_ONE_VARIABLE_SIZE_FIVE_PHASE_FIXTURE_ONLY**
