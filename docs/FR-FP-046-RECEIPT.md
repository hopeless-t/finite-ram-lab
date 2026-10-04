# FR-FP-046 Receipt

Status: **PASS / VARIABLE-SIZE EXACT WARM-BUDGET KNAPSACK QUALIFIED**

Parent: **FR-FP-045**

Final qualification:
- workflow run: 37217269606
- job: 111480217558
- execution head: 279f8366a2f7fc0bb74ebeac7fc31d60235769a9
- new physical runs: 0
- semantic values/deadline guards: reused unchanged from FR-FP-034

Frozen sizes for state IDs 0..9:

    4, 6, 8, 10, 12, 14, 16, 8, 8, 12 MiB

Deadline-mandatory WARM states remain:

    {7,8,9}

Mandatory physical bytes:

    28 MiB

Thus a 24 MiB request fails closed before optimization.

## Exact allocator

The dynamic-programming byte-budget allocator was compared with exhaustive
subset search across all frozen budgets:

    24, 28, 32, ... 96, 98 MiB

Result:

    DP vs exhaustive mismatches = 0

Every feasible exact solution:
- includes all mandatory WARM states;
- respects the existing deadline tolerance for every COLD state;
- has non-increasing expected COLD penalty as byte budget increases.

## Density-greedy observation

The equal-size-era density fill is not generally exact after sizes differ.

It loses to the exact allocator at 13 feasible budgets.

Examples:

40 MiB:
- greedy WARM {0,1,7,8,9}
- used 38 MiB
- expected COLD penalty 6.376661 ms
- exact WARM {0,2,7,8,9}
- used 40 MiB
- expected COLD penalty 6.161812 ms
- gap 0.214848 ms

64 MiB:
- greedy penalty 4.389238 ms
- exact penalty 3.539951 ms
- gap 0.849288 ms

80 MiB:
- greedy used 68 MiB
- greedy penalty 3.106394 ms
- exact used 80 MiB
- exact penalty 1.898544 ms
- gap 1.207849 ms

96 MiB:
- greedy used 82 MiB
- greedy penalty 1.641406 ms
- exact used 94 MiB
- exact penalty 0.433557 ms
- gap 1.207849 ms

Theory update:

**REPLACE_EQUAL_SIZE_DENSITY_FILL_WITH_EXACT_BYTE_BUDGET_KNAPSACK_WHEN_STATE_SIZES_DIFFER**

Resident capacity is now a byte constraint rather than a slot count.

Boundary:

This is one frozen heterogeneous size vector using FR-FP-034 semantic values.
No universal workload-size distribution is claimed.

Next:

Physically instantiate the heterogeneous files, compare exact and greedy
placement under the same byte-capacity contract, and separately calibrate
promotion/eviction cost against bytes rather than state count.

Claim ceiling:

**SYNTHETIC_VARIABLE_SIZE_ALLOCATION_USING_FP034_VALUES_AND_ONE_FROZEN_SIZE_VECTOR_ONLY**
