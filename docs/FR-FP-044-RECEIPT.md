# FR-FP-044 Receipt

Status: **PASS / BREAK-EVEN HORIZON INTERVAL GATE QUALIFIED**

Parent: **FR-FP-043**

Final qualification:
- workflow run: 37216371110
- job: 111477601436
- execution head: a21eac3595ef03d240476089e67b3bd69ced0672
- new physical runs: 0
- interval comparisons: 7,564
- mismatches: 0

Qualified law:

    H_star = migration_cost / benefit_per_round

Given a conservative validity-horizon interval:

    [H_lower, H_upper]

the Governor may stop horizon measurement when:

    H_lower >= H_star
        -> MIGRATE_CERTIFIED

or:

    H_upper < H_star
        -> HOLD_CERTIFIED

Only when:

    H_lower < H_star <= H_upper

does additional horizon evidence remain decision-relevant.

Safety remains an independent override.

Qualified break-even thresholds on the FR-FP-042/043 contexts:

- phase 1 -> 2: 60.5129 rounds
- phase 2 -> 3: 79.9918 rounds
- phase 3 -> 4: no placement change; no finite threshold
- phase 4 -> 5: 222.2253 rounds

This exactly explains the hosted H=100 policy:

    MIGRATE / MIGRATE / HOLD / HOLD

Representative interval decisions:

- phase 1->2 [20,50] -> HOLD certified
- phase 1->2 [50,70] -> more evidence required
- phase 1->2 [80,120] -> MIGRATE certified
- phase 4->5 [100,200] -> HOLD certified
- phase 4->5 [200,250] -> more evidence required

Evidence-surface biopsy incorporated:

The first successful scientific run emitted Python's non-standard JSON
`Infinity` for a no-change break-even value. The durable result was repaired
to:

    break_even_horizon_rounds = null
    break_even_reason = "NO_PLACEMENT_CHANGE"

without changing the scientific result.

Decision:

**STOP_HORIZON_MEASUREMENT_ONCE_THE_VALIDITY_INTERVAL_LIES_ENTIRELY_ON_ONE_SIDE_OF_BREAK_EVEN**

Meta consequence:

Exact horizon estimation is unnecessary once every admissible horizon implies
the same placement action.

Claim ceiling:

**ANALYTIC_HORIZON_INTERVAL_REDUCTION_ON_FP042_043_EQUAL_SIZE_MIGRATION_CONTEXTS_ONLY**
