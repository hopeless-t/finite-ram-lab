# FR-FP-045 — Robust horizon information-value ceiling

Status: **ANALYTIC INFORMATION-VALUE CANDIDATE**

Parent: **FR-FP-044**

## Why

FR-FP-044 says horizon measurement remains decision-relevant while the
conservative horizon interval straddles the break-even threshold.

Decision relevance alone is not enough.

Measurement itself costs time or resources.

The Governor should not pay more for information than the information can
possibly save.

## Distribution-free regret bound

For one ambiguous interval:

    [H_lower, H_upper]

let:

    Delta = semantic service benefit per round
    C = physical migration cost

If the Governor chooses HOLD, the worst-case regret is at H_upper:

    R_hold = max(0, Delta * H_upper - C)

If it chooses MIGRATE, the worst-case regret is at H_lower:

    R_migrate = max(0, C - Delta * H_lower)

Choose the robust action:

    argmin(R_hold, R_migrate)

The maximum amount perfect horizon information can remove from this robust
worst-case regret is bounded by:

    V_PI_ceiling = min(R_hold, R_migrate)

No horizon probability distribution is invented.

## Measurement gate

If:

    measurement_cost >= V_PI_ceiling

then even perfect information cannot justify the acquisition cost under this
robust regret bound.

Stop measuring and take the robust action.

If:

    measurement_cost < V_PI_ceiling

measurement can still be worth considering.

## Examples

Phase 1 -> 2, interval [50,70]:

- robust action: HOLD
- information-value ceiling: about 16.34 ms
- 5 ms measurement -> MEASURE MORE
- 20 ms measurement -> STOP

Phase 4 -> 5, interval [200,250]:

- robust action: MIGRATE
- information-value ceiling: about 10.43 ms
- 5 ms measurement -> MEASURE MORE
- 15 ms measurement -> STOP

## Exact check

Sweep the same FP44 horizon grid.

For every ambiguous interval compare the closed-form robust regret against an
exhaustive evaluation of every horizon grid point in the interval.

Qualification requires zero mismatches.

Also require the measurement decision to be monotonic in measurement cost.

## Boundary

Both measurement cost and regret are expressed in milliseconds here.

Do not generalize this comparison across heterogeneous units without an explicit
conversion contract.

## Meta consequence

The pruning rule is stronger now:

1. if information cannot change the decision, do not acquire it;
2. even if it can change the decision, do not acquire it when its maximum
   robust value is smaller than acquisition cost.

## Claim ceiling

**ANALYTIC_ROBUST_INFORMATION_VALUE_BOUND_ON_FP044_HORIZON_CONTEXTS_ONLY**
