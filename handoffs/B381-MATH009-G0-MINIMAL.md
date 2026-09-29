# B381 — Linux 7.0 fault-path audit + minimal argv/PTE alias breaker

## Status

Research-only bounce complete.

No scientific hosted run was launched.
No local-PC execution.

## Exact environment anchor

MEMCG-005G-F run:
`36577573774`

Exact job log confirms:
- Ubuntu 26.04.1 LTS
- runner image `ubuntu-26.04`
- image version `20260920.143.1`

Matching runner manifest reports:
`Linux 7.0.0-1012-azure`

Kernel-path audit was therefore repeated against upstream Linux `v7.0`.

## Main source-level mechanism result

User PTE allocation uses:

`GFP_PGTABLE_USER = ... | __GFP_ACCOUNT`

Page allocator routes accounted kernel pages through:

`__memcg_kmem_charge_page()`
-> `obj_cgroup_charge_pages()`
-> `try_charge_memcg()`
-> `consume_stock()`

Therefore new user page-table pages consume the same per-CPU memcg stock studied by Q64 experiments.

Anonymous write-fault ordering in Linux v7.0:

`pte_alloc()`
then
`alloc_anon_folio()`

This gives a concrete low-stock mechanism by which page-table state can alter the measured first-touch phenotype.

## Counter-audit

A naive uniform 2 MiB PTE-boundary model predicts only order `2/512 ~= 0.39%` sensitivity for an 8->10 page shift.

That is too small by itself to explain the observed G-F +5.14 percentage-point exact-zero split.

So:
- PTE/stock interaction remains plausible;
- naive single-boundary geometry is downgraded.

## mTHP

Default Linux policy:
- PMD-sized THP: inherit
- smaller mTHP sizes: never

G-F mapping maximum is 32 pages = 128 KiB, too small for a 2 MiB PMD THP.

No finite-ram-lab workflow override was found.

mTHP is downgraded.

## Receipt choice

Primary page-table receipt:

`/proc/<pid>/status : VmPTE`

Linux reports this from `mm_pgtables_bytes(mm)`, backed by an atomic counter.

Use:
- `VmPTE_pre_kib`
- `VmPTE_post_kib`
- `VmPTE_delta_kib`

Corroboration only:

`memory.stat:pagetables`

Reason:
memcg rstat flushing can skip small immediate updates until an update threshold is reached.

## Minimal argv alias breaker

Keep the C worker unchanged.

Direct same-capacity token intervention:

- C8: token `8` -> capacity 8
- P8: token `08` -> capacity 8
- C9: token `9` -> capacity 9
- P9: token `09` -> capacity 9
- H10: token `10` -> capacity 10
- H32: token `32` -> capacity 32

glibc `atoi()` calls decimal `strtol`, so zero-padding preserves numeric capacity.

Primary argv contrast:
`P8+P9 vs C8+C9`

Capacity-survival contrast:
`P8+P9 vs H10+H32`

## Monte Carlo calibration

Using G-F planning rates and REMOTE_LOW admission:

- 16 blocks / 960 candidates:
  - correct direction ~97.22%
  - correct direction + Fisher p<.05 ~42.66%
- 32 blocks / 1920:
  - direction ~99.76%
  - significance ~75.83%
- 48 blocks / 2880:
  - direction ~99.96%
  - significance ~90.69%

Recommended resource ladder:

`16 -> 32 -> 48 only as needed`

Stage A is instrument/direction discovery, not a negative test if p>=.05.

Each hosted stage requires Human compute approval.

## New documents

- `docs/MATH-009-LINUX7-FAULT-PATH-AUDIT.md`
- `docs/MEMCG-005G-G0-MINIMAL-ARGV-PTE-ALIAS-BREAKER-v1.md`
- `docs/MATH-010-G0-MONTE-CARLO-CALIBRATION.md`

## Rare-state construction route

Controlled induction b63 remains separate and alive.

If a verified Q64 primer is followed by construction of one residual stock page, the target/next-touch depth1 prediction remains the main route toward near-deterministic rare-state generation.

Do not claim natural specimens share that cause until G0/PTE evidence resolves.

## Stop

`HUMAN_COMPUTE_APPROVAL_FOR_G0_STAGE_A`

No 5760-candidate G-G launch.
