# B386 — PTE-preconditioned controlled-spawn implementation complete

## Status

IMPLEMENTED / CI PASS / NOT LAUNCHED.

No scientific controlled-spawn run was started.
No launch marker exists.
No local-PC execution.

## Motivation from G0

G0 Stage A established:

- argv width does not explain the old signal;
- capacity-associated LOW-state exact-zero survives width control;
- H32 uniquely triggers observed first-fault VmPTE +4 KiB;
- LOW PTE-growth specimens were 5/5 Q64;
- 12/19 LOW exact-zero specimens showed the R1/depth1 signature.

This motivates removing target-time PTE allocation before attempting deliberate stock construction.

## Construction

Use distinct CPUs:

- C = controller
- P = preparation
- S = stock / measured

Dedicated worker:

`experiments/memcg005gc_spawn_worker.c`

On P:

1. mmap 1024 pages;
2. choose a 192-page safe span wholly inside one PTE table;
3. touch one guard page;
4. thereby pre-establish PTE state;
5. expose geometry receipt.

Then migrate to S.

On S:

1. touch fresh pages inside the preconditioned PTE span;
2. observe first Q64 primer;
3. construct chosen residual stock phase;
4. measure target/follow-up pattern;
5. require VmPTE delta0 throughout measured phase.

## Frozen pilot arms

### b62

Consumed including primer:
62

Expected:
`ZERO -> ZERO -> Q64`

### b63

Consumed including primer:
63

Expected:
`ZERO -> Q64`

This is the primary rare-state spawn arm.

### b64

Consumed including primer:
64

Expected:
`Q64`

This is the boundary control.

## Pilot size

Frozen raw ceiling:

- 8 blocks
- 9 identities/block
- 72 raw candidates
- 24 raw candidates/arm
- replacement trials = false

Primer failures and mechanism failures remain outcomes.

No sample replacement.

## Implementation

Math/design:
`docs/MATH-013-PTE-PRECONDITIONED-SPAWN.md`

Protocol:
`docs/MEMCG-005G-C-CONTROLLED-RARE-INDUCTION-v2.md`

Worker:
`experiments/memcg005gc_spawn_worker.c`

Controller:
`src/finite_ram_lab/memcg005gc_controlled_spawn.py`

Spec:
`specs/MEMCG-005G-C-PTE-PRECONDITIONED-SPAWN-v2.json`

Tests:
`tests/test_memcg005gc_controlled_spawn.py`

Workflow:
`.github/workflows/memcg-005g-c-v2-controlled-spawn.yml`

## Failure taxonomy

- PRECONDITION_CPU_MISMATCH
- GEOMETRY_INVALID
- PRIMER_NOT_FOUND
- CALIBRATION_OTHER_DELTA
- PTE_CONTAMINATED
- CPU_OR_WORKER_ERROR
- SEQUENCE_EXHAUSTED
- BAIT_NONZERO
- OTHER_NONZERO_NONQ64
- NEXT_PHASE_MISMATCH

No silent retry.

## Evidence residency

Workflow already integrates:

- raw block retention 7 days;
- aggregate retention 30 days;
- full raw manifest;
- immediate manifest verification.

COLD archive can use the same byte-verified Drive flow proven in B385.

## Reliability ladder

Pilot is mechanism validation only.

If b63 becomes all-success:

- 24/24 -> one-sided 95% lower bound ~88.3%
- 59/59 -> >95%
- 96/96 -> ~96.9%
- 299/299 -> >99%

Do not call observed 100% literal certainty.

## Validation

CI:
`36594688827 = success`

Passed:
- compile
- full unit suite
- dedicated C worker syntax compile
- synthetic exact-pattern tests
- failure taxonomy
- Monte Carlo smoke
- environment smoke

## Stop

`HUMAN_SCIENTIFIC_LAUNCH_APPROVAL_FOR_CONTROLLED_SPAWN_V2_PILOT`

No physical spawn pilot has been launched.
