# B396 — OBS-004 closes counter-identity ambiguity

## Status

OBS-004 COMPLETE / SOURCE-GROUNDED INTERPRETATION / EVIDENCE COLD-VERIFIED.

Run:
\`36621525773\`

## Direct result

48 trials / 1,152 measured touches.

Exact -17:
12

Frozen aggregate:
- WORKER_LRU_BATCH 9
- SAME_COUNTER_ASYNC 3
- STOCK_DRAIN_SAME_COUNTER 0
- EXTERNAL_COINCIDENCE 0
- COUNTER_UNKNOWN 0
- TRACE_MISS 0

## Corrected interpretation

The three SAME_COUNTER_ASYNC specimens are not ordinary external coincidence.

Observed trigger tasks:
- .NET Tiered Com
- .NET TP Worker
- .NET Tiered Com

But their 17-page uncharge uses a page-counter pointer previously observed from the worker trial.

All three uncharge stacks are in the LRU/folio-batch family.

Linux source:

- cpu_fbatches is per-CPU shared state
- lru_add is not task- or memcg-private
- folio_batch_move_lru filters dead folios
- mem_cgroup_uncharge_folios uncharges each folio according to folio_objcg
- therefore current task can flush and uncharge folios owned by another memcg

Derived classes:

- SELF_TRIGGERED_WORKER_LRU_BATCH: 9
- CROSS_TASK_WORKER_OWNED_LRU_BATCH: 3
- STOCK_DRAIN_DIRECT: 0

## Core mechanism

The recurrent -17 contaminant is:

deferred worker-owned dead folios
+ shared per-CPU LRU-add batch
+ eventual batch flush by any task on that CPU
-> worker page_counter_uncharge(17)

Owner and trigger are distinct.

## Evidence

Raw:
- 128 files
- 7,465,126 bytes
- content-set SHA:
  81563042daa5459c32dbb9f77ffbc9395390cebae215ac47b80dcee0e6c4dfa5

Drive:
Catfood Lab Evidence/finite-ram-lab/OBS-004-PAGE-COUNTER-IDENTITY-v1/run-36621525773

5/5 BYTE-IDENTICAL PASS.

## Next

OBS-005:
controlled cross-cgroup LRU-batch handoff.

Goal:
intentionally create producer-owned dead folios in a shared per-CPU LRU-add batch, then let a second cgroup/task
fill and flush the batch.

Primary prediction:
producer memory.current drops when trigger task flushes producer-owned dead folios.

No b63 reliability scaling yet.
