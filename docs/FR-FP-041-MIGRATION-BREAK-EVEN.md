# FR-FP-041 — Physical migration break-even horizon

Status: **REUSED HOSTED PHYSICAL NEGATIVE-RESULT CANDIDATE**

Parent: **FR-FP-040**

## Why

FR-FP-038 showed that online value updates can improve expected COLD restore
cost by moving the five-slot WARM set.

FR-FP-039 physically executed those moves.

The semantic allocator did not price the physical migration itself.

FR-FP-041 asks whether the value improvement pays back the observed migration
cost within the 20-round evidence phase that motivated the new placement.

## Evidence reuse

No new hosted run.

Use:
- FR-FP-038 phase states and expected penalties;
- FR-FP-039 observed physical actuation times from workflow 37210203932.

Observed value-driven physical migrations:

- phase 1 -> 2: 99.916 ms
- phase 2 -> 3: 107.481 ms
- phase 3 -> 4: no placement change
- phase 4 -> 5: 102.495 ms

## Break-even law

At a new phase, compare:

    old placement penalty under new values

with:

    new optimal placement penalty

Define:

    benefit_per_round
      =
    old_penalty - new_penalty

Then:

    break_even_rounds
      =
    migration_cost / benefit_per_round

A migration is physically justified within a predicted validity horizon H only
if:

    H >= break_even_rounds

equivalently:

    H * benefit_per_round >= migration_cost

## Important separation

Do not hide migration cost inside the semantic value estimator.

Keep separate:
- expected restore-cost benefit;
- physical migration cost;
- expected placement validity horizon.

This preserves inspectability and allows policy to choose how conservative the
migration-cost estimate should be.

## Negative-result target

The frozen phase horizon is 20 rounds.

Qualification asks whether every observed value-driven migration needs more than
20 rounds to amortize.

If yes, the old immediate-optimum policy is not a physical optimum on this
fixture.

## Next

Build a hysteretic allocator that retains the current placement unless the
expected horizon benefit exceeds a conservative migration-cost estimate.

## Claim ceiling

**REUSED_HOSTED_ACTUATION_COST_BREAK_EVEN_ON_FP038_039_FIXED_CAPACITY_TRACE_ONLY**
