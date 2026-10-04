# FR-FP-036 — Dynamic WARM budget transition

Status: **DYNAMIC-BUDGET SHADOW CANDIDATE**

Parent: **FR-FP-035**

## Why

FR-FP-035 qualified semantic placement under one fixed 40 MiB WARM budget.

Real finite memory pressure moves.

The next Governor must change its resident set when the available WARM budget
changes.

## Frozen capacity schedule

Ten equal-size 8 MiB states.

WARM slots:

    5 -> 3 -> 7 -> 4 -> 6

Equivalent capacity:

    40 -> 24 -> 56 -> 32 -> 48 MiB

The state values and deadline guards remain the FR-FP-034 qualified shadow
fixture.

## Exact target set

For every phase:

1. compute the deadline-mandatory WARM states;
2. fill optional slots by value density;
3. compare against exhaustive search.

No approximate allocation is admitted in this lane.

## Minimal actuation

A naive controller could reissue a WARM/COLD action for all ten states after
every capacity change.

That work is unnecessary.

Only states in:

    old_warm_set XOR new_warm_set

change tier.

Therefore the exact minimal actuation set is the symmetric difference.

Unchanged state placement is decision-irrelevant actuation work.

## Infeasible pressure

Three states are deadline-mandatory WARM.

A separate two-slot budget is injected.

The Governor must not silently evict a mandatory state.

Expected route:

    MANDATORY_WARM_EXCEEDS_BUDGET
    -> FAIL CLOSED / escalate pressure response

This lane does not choose the escalation action.

## North-Star consequence

The Governor now has two adaptive axes:

- **which semantic state** occupies finite residency;
- **how the set changes** when available residency changes.

The control plane itself is also finite:

    only changed placements are actuated.

## Claim ceiling

**SYNTHETIC_DYNAMIC_CAPACITY_TRANSITIONS_ON_THE_FR_FP_034_EQUAL_SIZE_TEN_STATE_FIXTURE_ONLY**
