# MATH-009 — Linux 7.0 Fault-Path Audit for T10 / Exact-Zero

> **Status:** SOURCE-GROUNDED MECHANISM AUDIT
> **Input:** MEMCG-005G-F run 36577573774, Linux v7.0, GitHub runner image evidence
> **No causal claim. No hosted run launched.**

## 1. Exact hosted environment

MEMCG-005G-F run `36577573774` used `ubuntu-26.04`.

A job log from that exact run reports:

- Operating System: Ubuntu 26.04.1 LTS
- Runner Image: ubuntu-26.04
- Image Version: 20260920.143.1
- Included Software manifest: ubuntu26/20260920.143

The matching published runner manifest reports kernel:

`7.0.0-1012-azure`

The kernel-path audit below is therefore anchored to upstream Linux tag `v7.0`, rather than only current mainline.

## 2. User PTE pages are memcg-accounted

Linux v7.0 `include/asm-generic/pgalloc.h`:

`GFP_PGTABLE_USER = GFP_PGTABLE_KERNEL | __GFP_ACCOUNT`

and `pte_alloc_one()` allocates with `GFP_PGTABLE_USER`.

The page allocator routes `__GFP_ACCOUNT` pages through:

`__memcg_kmem_charge_page()`

Therefore a newly allocated user page-table page is a memcg-accounted kernel allocation.

## 3. PTE charge reaches the same per-CPU memcg stock

Linux v7.0 `mm/memcontrol.c` gives the chain:

`__memcg_kmem_charge_page()`
-> `obj_cgroup_charge_pages()`
-> `try_charge_memcg()`
-> `consume_stock()`

`consume_stock()` explicitly consumes stocked charge on the current CPU.

If local stock cannot satisfy the charge, `try_charge_memcg()` uses:

`batch = max(MEMCG_CHARGE_BATCH, nr_pages)`

This establishes a source-level connection between user page-table allocation and the same per-CPU memcg stock state machine studied by MEMCG-004/005.

## 4. Anonymous write-fault ordering

Linux v7.0 `mm/memory.c::do_anonymous_page()` performs:

1. `pte_alloc(vma->vm_mm, vmf->pmd)`
2. later `alloc_anon_folio(vmf)`

Thus page-table allocation can consume memcg stock before the anonymous data allocation on the measured first write fault.

This ordering is mechanistically important when residual stock is small.

## 5. Candidate low-stock state machine

Let `R` be usable same-CPU memcg stock immediately before the target write.

### Existing PTE page

Target needs only the data-page charge.

- R >= 1 -> target may consume stock and show delta0.
- R = 0 -> target data charge may trigger fresh Q64.

### New PTE page required

Target can require a page-table charge before the data-page charge.

- R >= 2 -> both charges may consume stock and target may still show delta0.
- R = 1 -> PTE can consume the last stocked page; subsequent data charge may trigger fresh Q64.
- R = 0 -> PTE itself may trigger a fresh batch before data allocation.

This is a candidate mechanism only. It must be tested prospectively.

## 6. Why this can connect T10 and depth1

A dominant natural low-stock population near R=1 would predict:

- if a suitable PTE page already exists: data consumes the last stock page -> exact-zero target -> next charge is Q64, producing a depth1 biopsy;
- if a new PTE page is required: the PTE allocation can consume the last stock page first -> the data page no longer presents as exact-zero.

Therefore a mapping/layout intervention that changes the probability of a new page-table allocation could change exact-zero capture probability without changing gross pre_current.

This provides one candidate bridge between:

- the CAP8/9 vs CAP10+ exact-zero rate difference;
- the dominant depth1 morphology.

It does not prove that bridge.

## 7. Counter-audit: simple 2 MiB boundary model is insufficient

On x86 with 4 KiB pages, one 4 KiB PTE page contains 512 PTE entries and covers 2 MiB.

Linux v7.0 x86 mmap ASLR is page-granular.

A naive uniform-phase model in which changing 8 pages to 10 pages matters only by crossing one 2 MiB PTE boundary gives order-of-magnitude probability:

`2 / 512 ~= 0.39%`

The observed MEMCG-005G-F exact-zero split is much larger:

- CAP8+9: 15/452 = 3.3186%
- CAP10+11+12+32: 78/922 = 8.4599%
- difference: +5.1413 percentage points

So the naive uniform single-boundary explanation is too weak by itself.

Possible remaining layout mechanisms include non-uniform VMA-gap phase, neighboring VMA structure, or other page-table state. These require receipts rather than speculation.

## 8. mTHP audit

Linux documentation states that by default:

- PMD-sized THP uses `enabled=inherit`;
- all other hugepage sizes use `enabled=never`.

The studied anonymous mapping is at most 32 base pages = 128 KiB in the G-F panel, too small to contain a 2 MiB PMD THP.

Therefore ordinary PMD-sized THP cannot explain the CAP8/9 vs CAP10+ split.

Small-size mTHP remains possible only if the hosted image explicitly overrides defaults; no such override exists in the finite-ram-lab workflow.

mTHP is therefore downgraded, not mathematically eliminated.

## 9. Receipt audit: VmPTE is stronger than memory.stat for a one-page delta

Linux v7.0 `/proc/<pid>/status` reports:

`VmPTE = mm_pgtables_bytes(mm) >> 10`

`mm_pgtables_bytes` is backed by an `atomic_long_t`, and `mm_inc_nr_ptes()` adds the PTE-table byte size directly.

This makes pre/post `VmPTE` a suitable per-process receipt for whether page-table memory grew across the measured target fault.

By contrast, `memory.stat` does expose `pagetables`, but its formatting path calls `mem_cgroup_flush_stats()`, whose implementation may skip a flush until the update delta exceeds a threshold.

Therefore:

- primary page-table receipt: `VmPTE_pre_kib`, `VmPTE_post_kib`, delta;
- corroborating cgroup receipt: `memory.stat:pagetables`;
- do not classify a 4 KiB PTE event solely from `memory.stat`.

## 10. Minimal-disturbance design principle

Do not modify the C worker merely to add address instrumentation in the first alias-break experiment.

Worker modification can itself change binary/VMA layout, exactly the substrate being studied.

Prefer:

1. unchanged MEMCG-005D worker;
2. controller-only argv-token intervention;
3. controller-only pre/post VmPTE observation;
4. existing memory.current endpoint.

Only if the effect survives should a second experiment instrument exact mapping addresses.

## 11. Council result

Mechanism ranking after source audit:

1. **memcg-stock / page-table interaction:** source-plausible and directly connected;
2. **mapping-length -> layout/page-table-state intervention:** plausible, requires prospective receipt;
3. **argv-width / exec-layout intervention:** real alias, cheap to falsify directly;
4. **small mTHP:** downgraded;
5. **naive uniform 2 MiB boundary crossing:** insufficient alone.

Next:

run a minimal zero-padding alias breaker with unchanged worker and VmPTE receipts before any 5760-candidate confirmatory replication.

Hosted research only.
No local-PC execution.
