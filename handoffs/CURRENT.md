# CURRENT

> Latest bounce: B381
> Stage: MATH-009 FAULT PATH COMPLETE / G0 MINIMAL DESIGN CALIBRATED
> Stop: HUMAN_COMPUTE_APPROVAL_FOR_G0_STAGE_A

## Main source-level finding

Linux v7.0 user PTE allocation is memcg-accounted and reaches the same per-CPU stock path:

`GFP_PGTABLE_USER (__GFP_ACCOUNT)`
-> `__memcg_kmem_charge_page()`
-> `obj_cgroup_charge_pages()`
-> `try_charge_memcg()`
-> `consume_stock()`

Anonymous write fault ordering:

`pte_alloc()`
then
`alloc_anon_folio()`

This makes page-table state a concrete candidate modulator of the first-touch Q64/exact-zero phenotype.

Doc:
`docs/MATH-009-LINUX7-FAULT-PATH-AUDIT.md`

## Exact hosted environment

G-F run `36577573774` exact job log:
- Ubuntu 26.04.1 LTS
- image `ubuntu-26.04`
- image version `20260920.143.1`

Matching image manifest:
- kernel `7.0.0-1012-azure`

## PTE receipt

Primary:
`VmPTE_pre_kib -> VmPTE_post_kib`

Corroboration only:
`memory.stat:pagetables`

Reason:
VmPTE reads atomic `mm_pgtables_bytes`; memcg rstat may suppress small immediate flushes.

## G0 minimal alias breaker

Doc:
`docs/MEMCG-005G-G0-MINIMAL-ARGV-PTE-ALIAS-BREAKER-v1.md`

Keep existing C worker unchanged.

Arms:
- C8=`8`
- P8=`08`
- C9=`9`
- P9=`09`
- H10=`10`
- H32=`32`

Primary:
`P8+P9 vs C8+C9`

This directly changes argv representation while holding numeric capacity fixed.

## Monte Carlo

Doc:
`docs/MATH-010-G0-MONTE-CARLO-CALIBRATION.md`

Planning ladder:
- 16 blocks / 960 total: direction ~97.22%, p<.05+direction ~42.66%
- 32 / 1920: ~99.76%, ~75.83%
- 48 / 2880: ~99.96%, ~90.69%

Recommended:
`16 -> 32 -> 48 only as needed`

Stage A is an instrument/direction probe.

## Counter-audits

- naive uniform 2 MiB boundary model alone is too weak (~0.39% order-of-magnitude crossing effect);
- default PMD THP cannot fit a <=128 KiB VMA;
- small mTHP is downgraded absent an explicit runner override.

## Rare-Pokemon construction

`docs/MEMCG-005G-C-CONTROLLED-RARE-INDUCTION-v1.md`

b63 remains the preferred near-deterministic depth1 construction route after G0 clarifies natural-state mechanism.

## Large replication

MEMCG-005G-G 5760-candidate replication remains DEFERRED.

## Authority

No G0 implementation/hosted launch yet.
No local-PC execution.
Each hosted stage requires Human compute approval.
