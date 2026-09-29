# CURRENT

> Latest bounce: B382
> Stage: TWO-TOUCH PTE/STOCK DISCRIMINATOR COMPLETE
> Stop: HUMAN_COMPUTE_APPROVAL_FOR_G0_STAGE_A

## Source-grounded mechanism

Linux v7.0:

`GFP_PGTABLE_USER (__GFP_ACCOUNT)`
-> `__memcg_kmem_charge_page()`
-> `obj_cgroup_charge_pages()`
-> `try_charge_memcg()`
-> `consume_stock()`

Anonymous first write:

`pte_alloc()`
then
`alloc_anon_folio()`

Thus page-table allocation can consume the same per-CPU memcg stock before the measured data-page charge.

Reference:
`docs/MATH-009-LINUX7-FAULT-PATH-AUDIT.md`

## G0 direct alias breaker

Use unchanged C worker.

Arms:
- C8 token 8
- P8 token 08
- C9 token 9
- P9 token 09
- H10 token 10
- H32 token 32

Primary:
`P8+P9 vs C8+C9`

Capacity-survival:
`P8+P9 vs H10+H32`

Reference:
`docs/MEMCG-005G-G0-MINIMAL-ARGV-PTE-ALIAS-BREAKER-v1.md`

## PTE receipt

Primary:
`VmPTE_pre -> VmPTE_post1`

Corroboration:
`memory.stat:pagetables`

VmPTE is preferred because it reads atomic per-mm page-table bytes while memcg rstat can defer small updates.

## New two-touch discriminator

For first-touch exact-zero specimens only, perform one additional adjacent touch.

Record:
- first VmPTE delta
- second touch memory.current delta
- second VmPTE delta

Ideal candidate states:

- VmPTE1 delta=0 + ZERO + second Q64 + VmPTE2 delta=0 -> R=1 candidate
- VmPTE1 delta>0 + ZERO + second Q64 + VmPTE2 delta=0 -> R=2 candidate
- VmPTE2 delta>0 -> boundary phenotype

Reference:
`docs/MATH-011-TWO-TOUCH-PTE-STOCK-DISCRIMINATOR.md`

## Quantitative constraint

Ideal one-PTE mediation:

`Delta ZERO = Delta P(existing PTE) * P(R=1)`

G-F observed difference:
`+5.1413 percentage points`

Therefore pure one-PTE mediation requires:
`P(R=1) >= 5.1413%`

## Historical biopsy

G-A:
- exact-zero specimens: 28
- depth1: 22/28 = 78.57%

Historical specimens lacked VmPTE, so existing-PTE/R1 and new-PTE/R2 depth1 cases could not be separated.

## Monte Carlo ladder

Reference:
`docs/MATH-010-G0-MONTE-CARLO-CALIBRATION.md`

- 16 blocks / 960: direction ~97.22%, Fisher-significant+direction ~42.66%
- 32 / 1920: ~99.76%, ~75.83%
- 48 / 2880: ~99.96%, ~90.69%

Recommended:
`16 -> 32 -> 48 only as needed`

Each hosted stage requires explicit Human compute approval.

## Rare-Pokemon construction

Controlled b63 route remains alive:

verified Q64 primer -> construct one residual stock page -> target -> predicted next Q64/depth1.

Do not merge natural-cause and constructed-state claims yet.

## Authority

No new scientific hosted run launched.
No local-PC execution.
MEMCG-005G-G 5760 replication remains DEFERRED.
