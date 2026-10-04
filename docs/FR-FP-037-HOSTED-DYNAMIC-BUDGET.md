# FR-FP-037 — Hosted physical dynamic WARM budget

Status: **HOSTED PHYSICAL DYNAMIC-BUDGET CANDIDATE**

Parent: **FR-FP-036**

## Question

Can the exact FR-FP-036 capacity transition contract actuate real page-cache
residency using only changed-state actions?

## Physical fixture

Ten durable regular-file states:

    10 x 8 MiB

Initial WARM capacity:

    5 slots = 40 MiB

Physical capacity schedule:

    5 -> 3 -> 7 -> 4 -> 6 slots

Equivalent resident targets:

    40 -> 24 -> 56 -> 32 -> 48 MiB

## Minimal actuation

The target WARM set at every phase is inherited from the exact FR-FP-036 shadow
allocator.

For each transition:

    changed = old_warm XOR new_warm

Only changed states receive DONTNEED or WARM prefetch actions.

Unchanged placements receive no redundant tier action.

Predicted total:

    11 physical actions

versus:

    40

for full ten-state re-enforcement after four transitions.

## Physical qualification

After every transition, observe all ten files with mincore.

Require:

- total resident MiB matches requested capacity;
- every target WARM state is >=95% resident;
- every target COLD state is <=10% resident;
- exactly the shadow-predicted changed states are actuated.

## Infeasible pressure

After the final 6-slot phase, inject:

    2-slot request

Three states remain deadline-mandatory WARM.

The allocator must return:

    MANDATORY_WARM_EXCEEDS_BUDGET

and perform:

    zero physical actions

The current physical placement must remain unchanged.

## North-Star consequence

Finite residency is now physically adaptive in two dimensions:

1. semantic state selection;
2. available resident capacity.

The control plane also obeys finite-working-set logic: unchanged tier actions are
not reissued.

## Claim ceiling

**HOSTED_PHYSICAL_DYNAMIC_CAPACITY_ACTUATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY**
