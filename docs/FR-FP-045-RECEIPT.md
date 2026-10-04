# FR-FP-045 Receipt

Status: **PASS / ROBUST HORIZON INFORMATION-VALUE CEILING QUALIFIED**

Parent: **FR-FP-044**

Final qualification:
- workflow run: 37216728740
- job: 111478633574
- full suite: 619 tests PASS
- interval comparisons: 7,564
- regret mismatches: 0
- new physical runs: 0

Qualified robust laws:

    R_hold
      =
    max(0, benefit_per_round * H_upper - migration_cost)

    R_migrate
      =
    max(0, migration_cost - benefit_per_round * H_lower)

    robust_action
      =
    argmin(R_hold, R_migrate)

    V_PI_ceiling
      =
    min(R_hold, R_migrate)

Measurement gate:

    if measurement_cost >= V_PI_ceiling:
        stop measurement
        take robust action

    else:
        measurement may continue

No horizon probability distribution is invented.

Representative phase 1 -> 2 interval [50,70]:
- robust action: HOLD
- HOLD worst-case regret: 16.344 ms
- MIGRATE worst-case regret: 18.111 ms
- perfect-information value ceiling: 16.344 ms
- measurement cost 5 ms -> MEASURE MORE
- measurement cost 20 ms -> STOP and HOLD

Representative phase 4 -> 5 interval [200,250]:
- robust action: MIGRATE
- HOLD worst-case regret: 13.030 ms
- MIGRATE worst-case regret: 10.426 ms
- perfect-information value ceiling: 10.426 ms
- measurement cost 5 ms -> MEASURE MORE
- measurement cost 15 ms -> STOP and MIGRATE

The measurement decision is monotonic in acquisition cost across the full
frozen grid.

Decision:

**MEASURE_HORIZON_ONLY_WHEN_THE_MAXIMUM_ROBUST_VALUE_OF_PERFECT_INFORMATION_EXCEEDS_MEASUREMENT_COST**

Meta consequence:

Decision relevance is necessary but not sufficient for keeping an information
acquisition process resident.

Even decision-relevant information should be pruned when the maximum robust
regret it can remove is no larger than its acquisition cost.

Boundary:

Measurement cost and regret are both milliseconds in this lane. No
cross-dimensional scalar conversion is claimed.

Claim ceiling:

**ANALYTIC_ROBUST_INFORMATION_VALUE_BOUND_ON_FP044_HORIZON_CONTEXTS_ONLY**
