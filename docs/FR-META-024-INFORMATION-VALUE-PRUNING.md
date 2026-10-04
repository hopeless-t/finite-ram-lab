# FR-META-024 — Information-value pruning capsule

Status: **META-COMPILATION CANDIDATE**

Parent: **FR-META-023**

Primary evidence:
- FR-FP-044 / PR #168
- FR-FP-045 / PR #169

## New pruning class

Decision-relevance pruning removes work that cannot change an admissible
decision.

FR-FP-045 established a second class:

> information may still be decision-relevant, but acquiring it is irrational
> when even perfect information cannot save more loss than acquisition costs.

Qualified analytic gate:

    information_value_ceiling <= acquisition_cost
      -> stop acquisition
      -> take the robust action

The resident capsule is:

    STOP_LOW_VALUE_INFORMATION_ACQUISITION

with action:

    STOP_INFORMATION_ACQUISITION_TAKE_ROBUST_ACTION

## Horizon proof adapter

The first domain adapter is deliberately narrow:

    horizon_measurement_question = true
    robust_information_value_bound_qualified = true
    measurement_cost_ge_information_value_ceiling = true

derives the generic proof facts needed by the capsule.

If the measurement cost is below the value ceiling, the compiler fails closed
and retains measurement.

## Catalog self-compression

Adding a new capsule is not permission to expand the resident catalog.

META-024 first compiles the overwhelmingly common:

    mc = SKIP

as the default disposition.

Only exceptional skills retain an explicit mc field:

- UNCHANGED
- REQUIRED
- CONDITIONAL

The emitted capsule still contains an explicit mc disposition, so behavior and
debuggability are preserved while repeated resident metadata is removed.

## Relationship to decision-relevance pruning

Decision irrelevance is the limiting case:

    maximum information value = 0

but the two skills remain separate in the resident catalog because:

- the proof contracts differ;
- low-value information can still change the decision;
- the selected fallback action is a robust decision rather than semantic
  equivalence.

A later proof may justify a deeper unification.

## Claim ceiling

**COMPILED_INFORMATION_VALUE_PRUNING_FOR_QUALIFIED_HORIZON_MEASUREMENT_CONTEXT_ONLY**
