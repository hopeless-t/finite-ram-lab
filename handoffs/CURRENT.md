# CURRENT

> **Latest bounce:** B302
> **Stage:** MEMCG-003 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## Accepted chain

MEMCG-001: `SUPPORT_H64`
MATH-001: `MODEL64_WINS`
MEMCG-002: naive durable per-CPU model rejected; seven-slot shared cache candidate retained.

## MEMCG-003 implementation

Files:
- `specs/MEMCG-003-SEVEN-SLOT-EVICTION-v1.json`
- `experiments/memcg003_holder.c`
- `src/finite_ram_lab/memcg003_seven_slot.py`
- `.github/workflows/memcg-003-seven-slot.yml`
- `tests/test_memcg003_seven_slot.py`

Intervention:
- fill 7 persistent wash memcgs on one CPU;
- insert persistent target;
- add distinct challengers;
- probe target after each insertion.

Controls:
- same-memcg repeated activity
- six-only challengers
- no-churn

Primary source prediction:
target eviction/fresh recharge near challenger #7.

Math:
- threshold E
- candidate K=1..10
- leave-one-block-out prediction
- discrete posterior over K

No launch marker exists.

## Next fresh-bounce action

Discover/read B302 ordinary CI exactly once.

- success -> explicit MEMCG-003 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
