# FR-FP-047 Receipt

Status: **PASS / HOSTED PHYSICAL VARIABLE-SIZE BYTE-BUDGET ALLOCATION QUALIFIED**

Parent: **FR-FP-046**

Final qualification:
- workflow run: 37218759543
- job: 111484607205
- execution head: 152cfe82b5c449362b6bc822dcf03e4aa1725cb0

Frozen state sizes:

    4, 6, 8, 10, 12, 14, 16, 8, 8, 12 MiB

Physical budget schedule:

    28 -> 40 -> 56 -> 72 -> 92 -> 44 MiB

Observed resident MiB:

    28 -> 40 -> 56 -> 72 -> 92 -> 44

Every phase exactly matched the exact DP knapsack allocation.

Qualified physical facts:
- WARM min residency = 1.0 for every phase
- COLD max residency = 0.0 for every phase
- physical actions: 16
- full re-enforcement reference: 50
- action reduction: 68%
- total prefetch bytes: 90,177,536 bytes
- infeasible 24 MiB request: 0 actions
- previous 44 MiB physical snapshot preserved exactly

Transition telemetry:
- 28->40: promote 12 MiB / evict 0 MiB / 16.034 ms
- 40->56: promote 16 MiB / evict 0 MiB / 17.648 ms
- 56->72: promote 26 MiB / evict 10 MiB / 31.395 ms
- 72->92: promote 26 MiB / evict 6 MiB / 31.447 ms
- 92->44: promote 6 MiB / evict 54 MiB / 62.376 ms

Failure biopsy before qualification:
- first run failed because the inherited 8 MiB prefetch primitive hid a fixed
  global SIZE_BYTES contract
- FR-FP-047 repaired this with a size-explicit actuator without changing the
  scientific schedule or allocator

Decision:

**PHYSICALLY_ENFORCE_EXACT_VARIABLE_SIZE_KNAPSACK_PLACEMENT_UNDER_A_BYTE_BUDGET**

Next:

Calibrate migration cost as a function of promoted bytes, evicted bytes and
direction instead of assuming one fixed cost per state.

Claim ceiling:

**HOSTED_PHYSICAL_VARIABLE_SIZE_ALLOCATION_ON_ONE_TEN_STATE_SIZE_VECTOR_AND_BUDGET_SCHEDULE_ONLY**
