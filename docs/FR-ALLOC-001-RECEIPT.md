# FR-ALLOC-001 — Fragmentation Surface Receipt

Status: **PASS / SYNTHETIC ALLOCATOR GEOMETRY VALIDATED**

## Qualification

- workflow run: 37119997367
- job: 111194093069
- execution head: 3f8f19ff163b0d4f008ebbe9bd2669f25be298a2
- artifact ID: 11272777473
- artifact ZIP SHA256: 8515390f8078ebd6c176b3c5362bba4a8ec9e32ce5fb5d462e51a1267f949560
- spec SHA256: c9f843dd02964255b546b642e56975a1975daf7cc1ad935c06aeb5bf487b95a3
- result SHA256: 5cdf1f2440827492bbb2c163cef9af88bdeb667b49940b8208f4210aa3256aba

## Canonical trace

The repository implementation freezes both seed and draw-domain identity.

A pre-commit pilot used different draw-domain labels and produced a different
deterministic trace. The canonical repository draw domains were frozen without
relaxing any qualification thresholds.

## Frozen result

- requests: 5,280
- MAX_RESERVE: 1,839 admitted / 3,441 rejected
- CONTIG_FIRST_FIT: 4,685 / 595
- contiguous rejects with enough total free capacity: 590
- PAGED: 4,787 / 493
- PAGED_PREFIX_SHARE: 5,056 / 224
- duplicate prefix blocks avoided: 12,904

Thus 590/595 = 99.1597% of contiguous-arm rejects occur despite enough total
free blocks.

PAGED_PREFIX_SHARE reduces rejects versus PAGED by 54.5639%.

## Internal fragmentation probe

- 16-token blocks: 0.7225% frozen waste
- 128-token blocks: 5.7859% frozen waste

## Main invariants

- total free capacity != allocatable contiguous capacity
- fragmentation can cause failure without changing semantic bytes
- prefix sharing attacks duplication after allocator geometry is improved
- allocator block size is itself a memory/performance control variable

## Claim ceiling

**SOURCE_GROUNDED_SYNTHETIC_ALLOCATOR_GEOMETRY_ONLY**
