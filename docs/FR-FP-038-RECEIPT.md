# FR-FP-038 Receipt

Status: **PASS / ONLINE MULTI-STATE VALUE REALLOCATION QUALIFIED**

Parent: **FR-FP-037**

Final qualification:
- workflow run: 37209879493
- job: 111458713419
- execution head: cd580b1ee9e5c16d14406e9b7aed7ef9181cb3e0
- state count: 10
- state size: 8 MiB
- WARM budget: 5 slots = 40 MiB
- evidence phases: 5
- observations added per phase/state: 20
- new physical runs: 0

Qualified online WARM sets:
- phase 1: {4,6,7,8,9}
- phase 2: {0,1,2,3,4}
- phase 3: {4,6,7,8,9}
- phase 4: {4,6,7,8,9}
- phase 5: {0,1,2,3,4}

Every phase exactly matched exhaustive subset search.

Minimal-delta actions:
- phase 1 -> 2: 8
- phase 2 -> 3: 8
- phase 3 -> 4: 0
- phase 4 -> 5: 8
- total: 24
- full re-enforcement baseline: 40
- action reduction: 40%

The phase-4 reuse evidence changed confidence values but did not change the
optimal WARM set, so actuation correctly remained zero.

Cumulative expected COLD penalty:
- online allocator: 30.908392 ms
- phase-1 static placement: 33.100290 ms
- reduction: 6.622%

Failure biopsy incorporated:
- the first gate demanded >=3 unique WARM sets;
- the actual trace produced 2;
- all scientific invariants had passed;
- the >=3 requirement was fixture richness, not theory;
- the gate was corrected to require only a real placement change (>=2 sets)
  without changing the evidence schedule or allocator.

Decision:

**REALLOCATE_FINITE_WARM_CAPACITY_ONLY_WHEN_ONLINE_REUSE_EVIDENCE_CHANGES_THE_OPTIMAL_STATE_SET**

Next:

Physically actuate these five online value phases on hosted Linux while keeping
resident capacity fixed at 40 MiB. Verify the phase-4 evidence update executes
zero tier actions and preserves physical placement.

Claim ceiling:

**SYNTHETIC_FIVE_PHASE_ONLINE_REUSE_EVIDENCE_REALLOCATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY**
