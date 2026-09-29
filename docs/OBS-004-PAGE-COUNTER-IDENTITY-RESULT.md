# OBS-004 — Page-counter identity result

> **Status:** COMPLETE / SOURCE-GROUNDED INTERPRETATION
> **Run:** \`36621525773\`
> **Launch/source commit:** \`e4981a18e591ce7877a7c418643d98693eb845b5\`
> **Purpose:** distinguish worker-owned uncharge from system-wide time coincidence.

## Frozen execution

- 4/4 blocks PASS
- 48/48 trials
- 24 measured touches/trial
- 1,152 measured touches
- no reliability-scale claim
- no dynamic expansion

## Frozen aggregate

Exact -17 events:
- 12

Classifier output:
- WORKER_LRU_BATCH: 9
- SAME_COUNTER_ASYNC: 3
- STOCK_DRAIN_SAME_COUNTER: 0
- EXTERNAL_COINCIDENCE: 0
- COUNTER_UNKNOWN: 0
- TRACE_MISS: 0

Worker page-counter cardinality:
- one counter: 26 trials
- two counters: 22 trials

Linux source explains why one or two leaf counters may appear: \`try_charge_memcg()\` may call
\`page_counter_try_charge()\` for memsw and memory separately.

## Nine direct worker-triggered specimens

Nine exact -17 specimens have:

\`worker LRU flush(31) -> worker folios_put(31) -> same worker page-counter uncharge(17)\`

The uncharge stack is the anonymous-fault LRU-add path.

These are direct repetitions of the OBS-002/003 dominant mechanism.

## Three SAME_COUNTER_ASYNC specimens

Three exact -17 specimens have no worker-comm LRU flush in the touch window, but the 17-page uncharge uses a
page-counter pointer previously observed from the current worker trial.

Observed current tasks:

- trial 2:9: \`.NET Tiered Com\`, shmem-fault LRU-add stack
- trial 3:6: \`.NET TP Worker\`, anonymous-fault LRU-add stack
- trial 3:9: \`.NET Tiered Com\`, shmem-fault LRU-add stack

All three selected 17-page events pass through the LRU/folio-batch family:

\`page_counter_uncharge -> folios_put_refs -> folio_batch_move_lru -> __folio_batch_add_and_move\`

Trial 3:9 is particularly strong:
the worker trial exposed exactly one page-counter pointer, and the .NET-triggered uncharge uses that same pointer.

## Source-grounded interpretation: cross-task LRU flush

Linux source provides the missing ownership semantics.

### Per-CPU shared batch

\`cpu_fbatches\` is defined with \`DEFINE_PER_CPU\`.

Its \`lru_add\` folio batch is protected by a CPU-local lock, not by task or memcg identity.

Therefore tasks running on the same CPU can add to and flush the same LRU-add batch.

### Dead-folio filtering

When an LRU-add batch is flushed, \`folio_batch_move_lru()\` filters dead folios into a temporary free batch.

It then calls:

\`mem_cgroup_uncharge_folios(&free_fbatch)\`

### Ownership follows the folio, not current task

\`uncharge_folio()\` reads:

\`objcg = folio_objcg(folio)\`

and \`uncharge_batch()\` resolves the memcg from that folio-owned objcg.

Therefore the task that triggers a batch flush can uncharge memory owned by a different cgroup/task.

This directly explains the SAME_COUNTER_ASYNC specimens:

1. worker-owned dead folios remain in the shared per-CPU LRU-add batch;
2. another task (.NET runner activity) adds a folio on that CPU;
3. that task fills/flushes the shared batch;
4. worker-owned dead folios are identified from their own objcg;
5. the worker's page counter is uncharged by 17;
6. worker \`memory.current\` falls even though the current task is not the worker.

The .NET task is therefore a **flush trigger**, not the owner of the released pages.

## Stock-drain status

No exact -17 event in OBS-004 is directly attributed to stock drain.

One SAME_COUNTER_ASYNC touch also contains a \`drain_stock\` event, but the selected 17-page uncharge stack is the
LRU/folio-batch path, not the stock-drain path.

Do not classify time-overlap alone as stock-drain causality.

## Revised -17 model

The recurrent -17 phenomenon is best described as:

\`deferred worker-owned dead folios + shared per-CPU LRU-add batch + eventual flush by any task on that CPU\`

Two trigger modes are observed:

- self-triggered flush by the worker;
- cross-task flush by another process on the same CPU.

The ownership and trigger are separate state dimensions.

This resolves the apparent contradiction in OBS-003 where a .NET task appeared in the stack while worker
\`memory.current\` fell.

## Meaning for finite-ram-lab

The observer contamination model should now include:

- charge owner;
- batch residency owner (CPU);
- flush trigger task;
- uncharge owner (folio memcg).

A process-centric observer is insufficient for shared kernel batching.

This is a concrete example of the lab's broader principle:

\`logical owner != physical staging location != transition trigger\`

## Evidence

Raw manifest:
- files: 128
- total bytes: 7,465,126
- content-set SHA-256:
  \`81563042daa5459c32dbb9f77ffbc9395390cebae215ac47b80dcee0e6c4dfa5\`

Aggregate artifact:
- \`OBS-004-PAGE-COUNTER-IDENTITY-36621525773\`
- SHA-256:
  \`23a28da2fabfeb203d354c1b45c60abb9379fa5910fbbc642897b26055c69cfc\`

Drive COLD locator:
\`Catfood Lab Evidence/finite-ram-lab/OBS-004-PAGE-COUNTER-IDENTITY-v1/run-36621525773\`

Drive re-download verification:
\`5 / 5 BYTE-IDENTICAL PASS\`

## Next

Before reliability scaling, one clean synthetic confirmation is valuable:

**OBS-005 cross-cgroup LRU-batch handoff**

Construct two cgroups/tasks pinned to the same CPU:

1. producer A adds a frozen number of anonymous folios to the per-CPU LRU-add batch;
2. A drops its mappings while keeping its cgroup alive;
3. trigger B fills the remaining batch slots;
4. observe B-triggered flush;
5. require A's page counter / memory.current to drop while B is current.

This turns the naturally occurring cross-task observation into an intentional state-transition test.
