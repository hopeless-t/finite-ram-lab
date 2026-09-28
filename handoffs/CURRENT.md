# CURRENT

> **Latest bounce:** B293
> **Stage:** MEMCG-002 CPU-STOCK CAUSAL DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## Accepted chain

MEMCG-001:
`SUPPORT_H64`

MATH-001:
`MODEL64_WINS`

Q64:
- exact reset-aware reconstruction
- minimum MDL
- held-out F1=1 in 4/4 folds

## Kernel mechanism

Upstream source:
- MEMCG_CHARGE_BATCH=64
- memcg_stock is per-CPU
- consume/refill operate on this_cpu_ptr(memcg_stock)
- one-page stock miss charges a 64-page batch and caches the remaining 63 pages locally

## MEMCG-002 frozen design

4 blocks x 4 arms = 16 trials:
- FIXED_TOUCH
- MIGRATE_TOUCH
- ROUNDTRIP_TOUCH
- ROUNDTRIP_CONTROL

Interventions:
- A->B after step128
- optional B->A after step192

Primary causal predictions:
- fresh B charge within 1-2 touches;
- post-migration Q64 spacing;
- old A phase restored on roundtrip;
- no positive events in migration-only control.

Design:
`docs/MEMCG-002-CPU-STOCK-CAUSAL-v1.md`

## Next fresh-bounce action

Implement:
- dedicated C migration worker
- schedule/spec
- event/phase analyzer
- causal verdict
- workflow
- tests

Do not launch during implementation.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
