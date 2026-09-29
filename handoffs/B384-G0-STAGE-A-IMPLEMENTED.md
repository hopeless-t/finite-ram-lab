# B384 — G0 Stage A implemented / not launched

## Status

IMPLEMENTATION COMPLETE / CI PASS / SCIENTIFIC RUN NOT LAUNCHED.

No launch marker exists.
No G0 scientific workflow run was started.
No local-PC execution.

## Goal

Implement the minimum-information-cost alias breaker that separates:

- canonical one-digit argv representation;
- zero-padded two-digit argv representation at the same numeric capacity;
- numeric capacity 10/32 anchors;
- first-fault page-table growth;
- exact-zero follow-up stock morphology.

## Frozen Stage A

16 independent hosted blocks.

60 candidates/block.

960 total candidates.

Six balanced arms, 10 candidates/arm/block:

- C8: token `8`, capacity 8
- P8: token `08`, capacity 8
- C9: token `9`, capacity 9
- P9: token `09`, capacity 9
- H10: token `10`, capacity 10
- H32: token `32`, capacity 32

Primary direct argv contrast:

`P8+P9 vs C8+C9`

Capacity-survival contrast:

`H10+H32 vs P8+P9`

Stage A is an instrument/direction probe, not a negative test when p>=.05.

## Worker preservation

The C worker remains exactly:

`experiments/memcg005d_worker.c`

No instrumentation was added to the worker binary.

This protects the exec/VMA-layout substrate under study.

## Controller receipts

For the first touch:

- memory.current delta
- VmPTE pre/post/delta
- memory.stat:pagetables pre/post/delta
- CPU match
- worker error
- touched count

VmPTE is primary page-table-growth receipt.

memory.stat:pagetables is corroboration only.

## Failure-only two-touch biopsy

Only after a valid REMOTE_LOW exact-zero first touch:

- issue exactly one adjacent second touch;
- record second memory.current delta;
- record second VmPTE delta.

Candidate classes:

- R1_CANDIDATE
- R2_CANDIDATE
- PTE_BOUNDARY
- OTHER
- INVALID

The second touch cannot alter the frozen first-touch endpoint.

## Environment receipts

Each block records:

- uname/kernel/platform
- libc metadata
- page size
- available CPUs
- worker SHA-256
- global THP setting
- every visible hugepages-*/enabled setting
- GitHub run/source metadata

This directly records whether small mTHP settings differ from the assumed defaults.

## Evidence Residency integration

Raw block artifacts:

`retention-days: 7`

Aggregate artifact:

`retention-days: 30`

Aggregate job downloads all raw blocks and creates:

`full-raw-evidence-manifest.json`

over the complete unpacked raw evidence tree.

The manifest is verified immediately with:

`frl evidence-verify`

before aggregate publication.

This allows later local/Google Drive COLD storage to be checked against the exact original content set.

No Drive credentials, uploads, or artifact deletion are embedded in the workflow.

## Implementation

Core:
`src/finite_ram_lab/memcg005gg0_alias_breaker.py`

Spec:
`specs/MEMCG-005G-G0-MINIMAL-ARGV-PTE-ALIAS-BREAKER-v1.json`

Tests:
`tests/test_memcg005gg0_alias_breaker.py`

Workflow:
`.github/workflows/memcg-005g-g0-alias-breaker.yml`

Design:
`docs/MEMCG-005G-G0-MINIMAL-ARGV-PTE-ALIAS-BREAKER-v1.md`

## Validation

CI run:

`36590212701 = success`

Passed:
- installation
- compileall
- full unit suite, including synthetic argv-like and capacity-like G0 worlds
- Monte Carlo smoke
- environment probe smoke

The G0 scientific workflow did not trigger on implementation commits.

## Authority boundary

STOP:

`HUMAN_SCIENTIFIC_LAUNCH_APPROVAL_FOR_G0_STAGE_A`

A separate launch checkpoint must create the launch marker or explicitly dispatch the workflow.

Large MEMCG-005G-G 5760-candidate replication remains DEFERRED.
