# CURRENT

> **Latest bounce:** B339
> **Stage:** MEMCG-005D IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## MEMCG-005C accepted result

Canonical:
`909b554048e4e269ebb644c8533857468cae8296`

Decision:
`REJECT_ATOMIC_PATH`

ATOMIC was worse than TWO_STEP in 4/4 blocks.

## MEMCG-005D implementation

Files:
- `specs/MEMCG-005D-EXTERNAL-MIGRATION-FIRST-TOUCH-v1.json`
- `experiments/memcg005d_worker.c`
- `src/finite_ram_lab/memcg005d_external_migration.py`
- `.github/workflows/memcg-005d-external-migration.yml`
- `tests/test_memcg005d_external_migration.py`

Shared-latch worker:
- READY / GO / DONE / STOP in prefaulted shared page;
- no measured-path FIFO/status I/O.

A/B:
- SELF_ATOMIC = worker self-migration then immediate touch;
- EXTERNAL_ATOMIC = controller migrates PID, confirms S, samples mid current, then GO triggers immediate touch.

EXTERNAL separately records:
- migration_delta_pages = mid - pre;
- touch_delta_pages = post - mid.

23 identities per arm per block.
4 blocks.

No launch marker exists.

## Next fresh-bounce action

Discover/read ordinary CI for B339 exactly once.

- success -> explicit MEMCG-005D hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
