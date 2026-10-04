# FR-FP-041 Receipt

Status: **PASS / PHYSICAL MIGRATION BREAK-EVEN NEGATIVE RESULT QUALIFIED**

Parent: **FR-FP-040**

- workflow run: 37213487396
- job: 111469207275
- execution head: 022e000c4f8e36b0b09b837e6e8c2542a3623a59
- shadow source: FR-FP-038
- physical actuation source: FR-FP-039 / workflow 37210203932
- new physical runs: 0
- fixed WARM budget: 5 slots = 40 MiB
- phase validity horizon: 20 rounds

Value-driven migrations:

1. phase 1 -> 2
   - expected benefit: 1.722778 ms/round
   - physical migration: 99.916 ms
   - break-even: 57.997 rounds
   - 20-round net value: -65.460 ms

2. phase 2 -> 3
   - expected benefit: 1.303263 ms/round
   - migration: 107.481 ms
   - break-even: 82.470 rounds
   - 20-round net value: -81.415 ms

3. phase 3 -> 4
   - placement unchanged
   - semantic benefit: 0
   - physical actuation: 0

4. phase 4 -> 5
   - expected benefit: 0.469120 ms/round
   - migration: 102.495 ms
   - break-even: 218.484 rounds
   - 20-round net value: -93.113 ms

Aggregate:
- expected 20-round semantic benefit: 69.903 ms
- observed migration cost: 309.891 ms
- benefit / migration ratio: 0.2256
- net value after migration: -239.988 ms

Decision:

**PRICE_PHYSICAL_MIGRATION_BEFORE_ACTUATION_AND_REQUIRE_EXPECTED_VALUE_TO_AMORTIZE_WITHIN_THE_PLACEMENT_VALIDITY_HORIZON**

Theory update:

Instantaneous semantic optimum is not the same as physical control optimum.

A placement change is admissible only after separating:
- expected service-cost improvement;
- physical migration cost;
- expected validity horizon.

The old immediate-optimum policy is a qualified negative result on this fixture:
all three physical swaps fail to amortize within the 20-round horizon.

Next:

Calibrate a conservative promote/evict migration-cost model on independent
physical transitions, validate it on held-out mixed swaps, then build a
hysteretic allocator.

Claim ceiling:

**REUSED_HOSTED_ACTUATION_COST_BREAK_EVEN_ON_FP038_039_FIXED_CAPACITY_TRACE_ONLY**
