# CURRENT

> **Latest bounce:** B292
> **Stage:** MATH-001 PASS / MODEL64_WINS / READY FOR CAUSAL PERTURBATION DESIGN
> **Turn stop reason:** READY_FOR_NEXT_DESIGN

## Accepted model result

MATH-001 run:
`36453581737`

Decision:
`MODEL64_WINS`

Q64:
- reset-aware SSE = 0
- MDL = 30 bits, minimum of all candidates
- trained Q = 64 in all 4 leave-one-block-out folds
- held-out precision/recall/F1 = 1.0 in every fold

Controls:
- zero positive events

Canonical result:
`docs/MATH-001-RESULT.md`

## Current system-law candidate

On the tested Ubuntu 26.04 / kernel 7.0.0-1012-azure / cgroup-v2 substrate:

**memory.current behaves as a resettable 64-page accounting staircase under one-page anonymous touches.**

This is a Linux accounting-system result, not a DRAM hardware law.

## Kernel mechanism candidate

Inspected upstream source:
- `MEMCG_CHARGE_BATCH = 64U`
- `memcg_stock` is `DEFINE_PER_CPU_ALIGNED`
- accesses use `this_cpu_ptr(&memcg_stock)`

Therefore CPU identity is a direct causal intervention target.

## Next fresh-bounce action

Freeze MEMCG-002 causal design.

Core comparison:
- fixed CPU throughout;
- deliberate one-time CPU migration mid-trial;
- migration without touches control.

Primary question:
does migration change staircase phase/reset state while preserving Q=64?

Do not launch during design bounce.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
