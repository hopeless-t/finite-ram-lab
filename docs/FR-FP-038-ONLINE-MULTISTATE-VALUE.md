# FR-FP-038 — Online state value under one finite WARM budget

Status: **SYNTHETIC ONLINE-VALUE REALLOCATION CANDIDATE**

Parent: **FR-FP-037**

## Why

FR-FP-037 physically moved the WARM budget while state values were fixed.

A real Governor also faces the opposite problem:

    capacity stays finite,
    but semantic value changes as new reuse evidence arrives.

FR-FP-038 freezes WARM capacity at:

    5 x 8 MiB = 40 MiB

and updates each state's conservative reuse value over five evidence phases.

## Online evidence

Every phase adds 20 Bernoulli reuse opportunities per state.

Cumulative reuse counts are converted to exact one-sided 95% Clopper-Pearson
upper bounds.

State value is:

    v_i
      =
    p_upper_i
      * E[(bR-W)+]

The hosted baseline and empirical restore priors remain frozen from earlier
qualified lanes.

## Allocation

At every phase:

1. recompute each state value from cumulative evidence;
2. apply the deadline-risk guard;
3. allocate exactly five equal-size WARM slots by descending value;
4. compare the result with exhaustive subset search;
5. emit only the symmetric difference from the previous WARM set.

If new evidence does not change the optimal WARM set:

    actuation_count = 0

even though observations were added.

## Static control

Freeze the phase-1 WARM set and carry it through all later phases.

Compare cumulative expected COLD penalty with the online allocator.

This tests whether observing state value without changing placement is itself
wasteful.

## Qualification

Require:

- every phase exact-matches exhaustive optimum;
- at least three distinct optimal WARM sets;
- at least one later evidence phase with zero actuation;
- minimal delta actions beat full re-enforcement;
- online reallocation beats phase-1 static placement.

## North-Star consequence

Finite RAM now treats semantic placement as online sufficient state:

    new evidence
      -> compact value update
      -> decision changes?
         no  -> zero action
         yes -> actuate only changed state tiers

This is the same decision-relevance rule now applied to multi-state placement.

## Claim ceiling

**SYNTHETIC_FIVE_PHASE_ONLINE_REUSE_EVIDENCE_REALLOCATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY**
