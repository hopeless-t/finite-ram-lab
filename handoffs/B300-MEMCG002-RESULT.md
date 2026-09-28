# Bounce Handoff

> **Bounce ID:** B300
> **Status:** COMPLETE / MEMCG-002 PASS / NAIVE PER-CPU MODEL REJECTED

Run:
`36456299417`

Decision:
`REJECT_PERCPU_STOCK`

Full support blocks:
`0/4`

But:
- FIXED_TOUCH: 4/4 PASS
- ROUNDTRIP_CONTROL: 4/4 PASS
- MIGRATE_TOUCH: 3/4 PASS
- ROUNDTRIP_TOUCH: 1/4 PASS

Model exceptions:
- GLOBAL_PHASE = 31
- PERCPU_PHASE = 11

Thus CPU-conditioned state remains favored, but the preregistered durable one-stock-per-CPU model is too simple.

Source correction:
`NR_MEMCG_STOCK = 7`.

Each CPU owns a seven-slot shared memcg charge cache with drain/eviction, not a permanent target-memcg phase register.

Canonical result:
`docs/MEMCG-002-RESULT.md`

Next:
freeze MEMCG-003 as a direct seven-slot occupancy/eviction experiment.

Hosted research only.
No local-PC execution.
