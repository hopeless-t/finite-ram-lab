# FR-FP-040 Receipt

Status: **PASS / HOSTED COMBINED CAPACITY + VALUE GOVERNOR QUALIFIED**

Parent: **FR-FP-039**

- workflow run: 37213127651
- job: 111468146877
- execution head: 20213513d01ec63ae5de1fb33c9737de53260711
- states: 10
- state size: 8 MiB
- phases: 5
- capacity schedule: 5 -> 3 -> 7 -> 4 -> 6 slots
- resident target: 40 -> 24 -> 56 -> 32 -> 48 MiB

Qualified physical WARM sets:

1. 5 slots:
   - {4,6,7,8,9}

2. 3 slots:
   - {0,1,2}

3. 7 slots:
   - {2,4,5,6,7,8,9}

4. 4 slots:
   - {6,7,8,9}

5. 6 slots:
   - {0,1,2,3,4,9}

Every shadow allocation exactly matched exhaustive search.

Hosted physical residency:
- phase 1: 40 MiB
- phase 2: 24 MiB
- phase 3: 56 MiB
- phase 4: 32 MiB
- phase 5: 48 MiB

Every WARM state was physically resident.
Every COLD state was physically nonresident.

Minimal-delta physical transitions:
- 1 -> 2: 8 actions / 81.083 ms
- 2 -> 3: 8 actions / 74.467 ms
- 3 -> 4: 3 actions / 32.119 ms
- 4 -> 5: 8 actions / 77.034 ms

Totals:
- physical actions: 27
- full re-enforcement baseline: 40
- action reduction: 32.5%
- PREFETCH bytes: 112 MiB

Decision:

**RECOMPUTE_THE_OPTIMAL_MULTI_STATE_WARM_SET_FROM_CURRENT_CAPACITY_AND_CURRENT_SEMANTIC_VALUE_THEN_PHYSICALLY_ACTUATE_ONLY_THE_SET_DIFFERENCE**

Theory update:

Capacity and semantic-value changes are different upstream causes but collapse
to one downstream control primitive:

    old admissible placement
      vs
    new admissible placement
      ->
    physically execute only the set difference

New failure surface:

Physical migration itself costs tens of milliseconds in this fixture. A newly
optimal set should therefore not automatically be enacted if the expected value
improvement cannot amortize the migration cost over its expected validity
horizon.

Next:

Price physical actuation and compute transition break-even horizons before
adding hysteresis.

Claim ceiling:

**HOSTED_PHYSICAL_COMBINED_CAPACITY_VALUE_CONTROL_ON_ONE_TEN_STATE_EQUAL_SIZE_FIVE_PHASE_FIXTURE_ONLY**
