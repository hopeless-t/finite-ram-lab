# FR-FP-040 — Hosted combined capacity + semantic-value Governor

Status: **HOSTED PHYSICAL COMBINED-CONTROL CANDIDATE**

Parent: **FR-FP-039**

## Why

Two control dimensions are already qualified independently.

FR-FP-036/037:
- WARM capacity changes over time;
- optimal placement changes;
- only the symmetric difference is actuated.

FR-FP-038/039:
- semantic state value changes from online reuse evidence;
- optimal placement changes;
- only the symmetric difference is actuated.

FR-FP-040 combines both in one phase clock.

## Five phases

Online reuse evidence is the frozen FR-FP-038 schedule.

WARM capacity is:

    5 -> 3 -> 7 -> 4 -> 6 slots

Each state is 8 MiB.

Therefore physical target residency is:

    40 -> 24 -> 56 -> 32 -> 48 MiB

At every phase:

1. update conservative per-state reuse/value evidence;
2. solve the current finite-budget WARM allocation;
3. verify the greedy equal-size allocation against exhaustive search;
4. compare the new optimal WARM set with the previous set;
5. physically actuate only the symmetric difference;
6. verify WARM/COLD page-cache residency.

## One downstream primitive

Capacity changes and semantic-value changes enter the allocator differently, but
after optimization they collapse to the same action contract:

    old admissible decision
      vs
    new admissible decision
      ->
    actuate only the set difference

Unchanged placements remain resident and receive no redundant tier action.

## Qualification

Require:

- all five shadow allocations match exhaustive optimum;
- hosted physical WARM sets equal shadow sets;
- physical resident MiB equals the current capacity at every phase;
- every WARM state is physically resident;
- every COLD state is physically nonresident;
- physical action count equals shadow symmetric-difference count;
- minimal delta uses fewer actions than full ten-state re-enforcement.

## Next

Once both capacity and value can move together, the next likely failure mode is
thrash:

> small value changes can repeatedly swap marginal states even when the expected
> benefit is smaller than the physical migration cost.

The next lane should therefore price actuation itself and test hysteresis.

## Claim ceiling

**HOSTED_PHYSICAL_COMBINED_CAPACITY_VALUE_CONTROL_ON_ONE_TEN_STATE_EQUAL_SIZE_FIVE_PHASE_FIXTURE_ONLY**
