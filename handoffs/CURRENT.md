# CURRENT

> Latest bounce: B386
> Stage: PTE-PRECONDITIONED CONTROLLED SPAWN IMPLEMENTED / CI PASS / NOT LAUNCHED
> Stop: HUMAN_SCIENTIFIC_LAUNCH_APPROVAL_FOR_CONTROLLED_SPAWN_V2_PILOT

## Previous result: G0 Stage A

Run:
`36591417373 = success`

Key findings:

- argv-width explanation not supported;
- capacity signal survives width control;
- H32 uniquely produced first-fault VmPTE +4 KiB;
- LOW PTE-growth was 5/5 Q64;
- 12/19 LOW exact-zero specimens were R1 candidates;
- small mTHP disabled;
- Drive COLD replica 17/17 byte-identical.

Docs:
- `docs/MEMCG-005G-G0-STAGE-A-RESULT.md`
- `docs/MATH-012-G0-SENSITIVITY-AND-PTE.md`

## Controlled-spawn v2

Goal:

convert rare LOW exact-zero/depth1 from natural capture into constructed state.

CPU roles:

- C controller
- P preparation
- S stock/measured

On P:

`mmap -> choose same-PTE safe span -> touch guard -> PTE precondition`

Then migrate to S.

On S:

`find fresh Q64 -> consume exact stock count -> target/follow-up pattern`

All measured touches must have:

`VmPTE_delta = 0`

## Arms

b62:

`ZERO -> ZERO -> Q64`

b63:

`ZERO -> Q64`

b64:

`Q64`

b63 is primary spawn arm.

## Pilot freeze

- 8 blocks
- 9 raw identities/block
- 72 raw total
- 24 raw/arm
- no replacement trials

## Implementation

Math:
`docs/MATH-013-PTE-PRECONDITIONED-SPAWN.md`

Protocol:
`docs/MEMCG-005G-C-CONTROLLED-RARE-INDUCTION-v2.md`

Worker:
`experiments/memcg005gc_spawn_worker.c`

Controller:
`src/finite_ram_lab/memcg005gc_controlled_spawn.py`

Spec:
`specs/MEMCG-005G-C-PTE-PRECONDITIONED-SPAWN-v2.json`

Workflow:
`.github/workflows/memcg-005g-c-v2-controlled-spawn.yml`

## Validation

CI:
`36594688827 = success`

Scientific spawn workflow has NOT run.

No launch marker exists.

## Evidence policy

- raw HOT 7 days
- aggregate HOT 30 days
- full raw manifest + verify
- COLD Google Drive/local after run

## Reliability interpretation

Pilot tests mechanism only.

All-success b63 reliability ladder:

- 24 -> lower95 ~88.3%
- 59 -> >95%
- 96 -> ~96.9%
- 299 -> >99%

Do not claim literal 100%.

## Authority

No physical controlled-spawn run authorized yet.
No local-PC execution.
No larger runner.
No paid resource.
