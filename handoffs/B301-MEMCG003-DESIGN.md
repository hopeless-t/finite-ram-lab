# Bounce Handoff

> **Bounce ID:** B301
> **Status:** COMPLETE / MEMCG-003 SEVEN-SLOT EVICTION DESIGN FROZEN

MEMCG-002 result:
- preregistered naive durable per-CPU model rejected;
- PERCPU_PHASE still beats GLOBAL_PHASE by exceptions 11 vs 31;
- source inspection reveals `NR_MEMCG_STOCK = 7`.

MEMCG-003 directly tests the seven-slot structure.

Core intervention:
- fill 7 persistent wash memcgs on one CPU;
- insert persistent target memcg;
- add distinct persistent challenger memcgs one-by-one;
- probe target after every insertion;
- source model predicts target eviction/recharge around challenger #7.

Controls:
- same-memcg repeated activity;
- six-only challengers;
- no-churn wall-clock control.

Math:
- discrete threshold E;
- candidate K=1..10;
- MDL threshold model;
- Bayesian categorical K posterior;
- leave-one-block-out prediction.

Next:
implement only. Do not launch in implementation bounce.

Hosted research only.
No local-PC execution.
