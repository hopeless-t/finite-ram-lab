# CURRENT

> Latest bounce: B384
> Stage: G0 STAGE A IMPLEMENTED / CI PASS / NOT LAUNCHED
> Stop: HUMAN_SCIENTIFIC_LAUNCH_APPROVAL_FOR_G0_STAGE_A

## G0 Stage A

Frozen scale:

- 16 hosted blocks
- 60 candidates/block
- 960 total candidates
- 160 raw candidates/arm

Arms:

- C8 = token 8 / capacity 8
- P8 = token 08 / capacity 8
- C9 = token 9 / capacity 9
- P9 = token 09 / capacity 9
- H10 = token 10 / capacity 10
- H32 = token 32 / capacity 32

Primary direct argv contrast:

`P8+P9 vs C8+C9`

Capacity-survival contrast:

`H10+H32 vs P8+P9`

Stage A role:

`INSTRUMENT_AND_DIRECTION_PROBE`

Do not interpret p>=.05 at Stage A as evidence against argv.

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

Unchanged worker:
`experiments/memcg005d_worker.c`

## PTE / stock receipts

First touch records:

- memory.current delta
- VmPTE pre/post/delta
- memory.stat:pagetables corroboration
- CPU/touched/error receipts

Exact-zero first specimens receive exactly one second adjacent touch.

Candidate classifications:

- R1_CANDIDATE
- R2_CANDIDATE
- PTE_BOUNDARY
- OTHER
- INVALID

## Environment receipt

Each block records:

- kernel/platform
- libc
- page size
- CPUs
- worker SHA-256
- THP global setting
- all visible hugepages-*/enabled settings

## Evidence Residency

Raw blocks:
`7 days`

Aggregate:
`30 days`

Aggregate contains:
- summary.json
- full-raw-evidence-manifest.json

The full raw tree is manifest-hashed and immediately verified before aggregate publication.

After the run, raw evidence may be demoted to local/Google Drive only after restored-copy verification.

## Validation

CI:
`36590212701 = success`

The scientific G0 workflow did NOT run during implementation.

## Research mechanism

B382 remains active:

Linux v7.0 page-table charge reaches the same per-CPU memcg stock before anonymous data allocation.

MATH-011 two-touch discriminator remains the prospective mechanism test.

## Authority

No G0 launch marker exists.

No scientific hosted run launched.

No local-PC execution.

Large 5760-candidate G-G remains DEFERRED.
