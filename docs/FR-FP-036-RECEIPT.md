# FR-FP-036 Receipt

Status: **PASS / DYNAMIC WARM-BUDGET MINIMAL-ACTUATION CONTRACT QUALIFIED**

Parent: **FR-FP-035**

- workflow run: 37205213210
- state count: 10
- state size: 8 MiB
- capacity schedule: 5 -> 3 -> 7 -> 4 -> 6 WARM slots
- exhaustive allocation match: PASS at every phase

Qualified optimal WARM sets:

1. 5 slots / 40 MiB:
   - {5,6,7,8,9}

2. 3 slots / 24 MiB:
   - {7,8,9}

3. 7 slots / 56 MiB:
   - {3,4,5,6,7,8,9}

4. 4 slots / 32 MiB:
   - {6,7,8,9}

5. 6 slots / 48 MiB:
   - {4,5,6,7,8,9}

## Minimal transition actions

5 -> 3:
- evict {5,6}
- 2 actions instead of 10

3 -> 7:
- promote {3,4,5,6}
- 4 actions instead of 10

7 -> 4:
- evict {3,4,5}
- 3 actions instead of 10

4 -> 6:
- promote {4,5}
- 2 actions instead of 10

Total:
- minimal actions: 11
- full re-enforcement actions: 40
- actuation reduction: 72.5%

Unchanged placements are not reissued.

## Infeasible pressure

Injected budget:

    2 slots = 16 MiB

Deadline-mandatory WARM count:

    3

Result:

    MANDATORY_WARM_EXCEEDS_BUDGET
    -> infeasible / fail closed

The allocator does not silently evict a mandatory state.

Decision:

**ACTUATE_ONLY_THE_SYMMETRIC_DIFFERENCE_BETWEEN_OLD_AND_NEW_OPTIMAL_WARM_SETS_AND_FAIL_CLOSED_BELOW_MANDATORY_CAPACITY**

Next:

Physically apply the same dynamic capacity schedule with DONTNEED/PREFETCH only
on changed states, and verify page-cache residency after every phase.

Claim ceiling:

**SYNTHETIC_DYNAMIC_CAPACITY_TRANSITIONS_ON_THE_FR_FP_034_EQUAL_SIZE_TEN_STATE_FIXTURE_ONLY**
