# CURRENT

> **Latest bounce:** B301
> **Stage:** MEMCG-003 SEVEN-SLOT EVICTION DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## Accepted chain

MEMCG-001:
`SUPPORT_H64`

MATH-001:
`MODEL64_WINS`

MEMCG-002:
`REJECT_PERCPU_STOCK` for the naive durable one-stock-per-CPU model.

But:
- FIXED_TOUCH 4/4 PASS
- ROUNDTRIP_CONTROL 4/4 PASS
- MIGRATE_TOUCH 3/4 PASS
- ROUNDTRIP_TOUCH 1/4 PASS
- PERCPU_PHASE exceptions 11 vs GLOBAL_PHASE 31

## Source correction

Upstream Linux defines:
`NR_MEMCG_STOCK = 7`

Each CPU has a seven-slot shared memcg charge cache with rotating drain/eviction.

## MEMCG-003

Frozen design:
`docs/MEMCG-003-SEVEN-SLOT-EVICTION-v1.md`

Core test:
- fill 7 persistent wash memcgs on one CPU;
- insert target;
- add persistent distinct challengers one by one;
- probe target stock survival;
- infer first eviction threshold E.

Source prediction:
`E ~= 7`

Candidate K:
`1..10`

Controls:
- same-memcg activity
- six-only
- no-churn

Analysis:
- threshold error
- MDL
- Bayesian discrete K posterior
- leave-one-block-out prediction
- counterexample reporting

## Next fresh-bounce action

Implement MEMCG-003 only:
- persistent holder worker
- interactive target worker
- orchestration
- analyzer
- tests
- hosted workflow

Do not launch during implementation.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
