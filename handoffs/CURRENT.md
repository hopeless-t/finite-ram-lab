# CURRENT

> **Latest bounce:** B294
> **Stage:** MEMCG-002 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## MEMCG-002 implementation

Files:
- `specs/MEMCG-002-CPU-STOCK-CAUSAL-v1.json`
- `experiments/memcg002_worker.c`
- `src/finite_ram_lab/memcg002_cpu_stock.py`
- `.github/workflows/memcg-002-cpu-stock.yml`
- `tests/test_memcg002_cpu_stock.py`

4 arms per block:
- FIXED_TOUCH
- MIGRATE_TOUCH
- ROUNDTRIP_TOUCH
- ROUNDTRIP_CONTROL

4 blocks / 16 trials.

Key causal predictions:
- migration to B produces first +64 within 1-2 touches;
- B-side events retain Q64 spacing;
- A roundtrip restores old A phase;
- migration-only control has zero positive events.

No launch marker exists.

## Next fresh-bounce action

Discover/read B294 ordinary CI exactly once.

- success -> explicit MEMCG-002 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
