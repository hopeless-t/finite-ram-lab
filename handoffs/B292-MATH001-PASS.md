# Bounce Handoff

> **Bounce ID:** B292
> **Status:** COMPLETE / MATH-001 PASS / MODEL64_WINS

Run `36453581737`: PASS.

Decision:

`MODEL64_WINS`

Q64:
- reset-aware SSE = 0
- total MDL = 30 bits
- leave-one-block-out F1 = 1.0 in 4/4 folds
- controls positive events = 0

Kernel source consistency:
- MEMCG_CHARGE_BATCH = 64
- memcg_stock is per-CPU
- current-CPU stock accessed through this_cpu_ptr

Next:
freeze MEMCG-002 as a CPU-migration causal perturbation study.

Hosted first.
No local execution.
