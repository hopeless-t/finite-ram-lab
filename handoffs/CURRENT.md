# CURRENT

> Latest bounce: B396
> Stage: -17 DOMINANT MECHANISM = SHARED PER-CPU LRU-BATCH RELEASE
> Stop: READY FOR OBS-005 CONTROLLED CROSS-CGROUP HANDOFF

## OBS-004

Run:
\`36621525773 = success\`

Scale:
- 48 trials
- 1152 touches

Exact -17:
12

Frozen aggregate:
- WORKER_LRU_BATCH 9
- SAME_COUNTER_ASYNC 3
- STOCK_DRAIN_SAME_COUNTER 0
- EXTERNAL_COINCIDENCE 0
- COUNTER_UNKNOWN 0
- TRACE_MISS 0

## Source-grounded reinterpretation

Derived:
- SELF_TRIGGERED_WORKER_LRU_BATCH 9
- CROSS_TASK_WORKER_OWNED_LRU_BATCH 3
- STOCK_DRAIN_DIRECT 0

Why:

Linux lru_add folio batching is per-CPU shared state.

At flush:
- dead folios are filtered into a free batch
- uncharge uses folio_objcg
- the current task need not own the released folios

Thus a .NET task can trigger a flush that lowers the worker cgroup's memory.current.

## Mechanism

logical folio owner
!=
physical batching location
!=
flush trigger task

Recurrent -17 is observer contamination from deferred LRU release, not residual-stock consumption.

## Evidence

Doc:
docs/OBS-004-PAGE-COUNTER-IDENTITY-RESULT.md

Raw:
- files 128
- bytes 7,465,126
- SHA:
  81563042daa5459c32dbb9f77ffbc9395390cebae215ac47b80dcee0e6c4dfa5

Drive:
Catfood Lab Evidence/finite-ram-lab/OBS-004-PAGE-COUNTER-IDENTITY-v1/run-36621525773

Verification:
5/5 BYTE-IDENTICAL PASS.

## Next

OBS-005 controlled cross-cgroup LRU-batch handoff.

Construct:
- producer cgroup A
- trigger cgroup B
- same CPU
- producer leaves a controlled dead-folio population in LRU-add batch
- trigger fills remaining slots
- observe producer page-counter drop while trigger is current

## Authority

HOSTED_RESEARCH_ONLY.
No local-PC execution.
No paid runner.
No b63 reliability scaling yet.
