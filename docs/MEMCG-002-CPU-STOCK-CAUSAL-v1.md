# MEMCG-002 CPU-Stock Causal Perturbation v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Scientific question

Does deliberate CPU migration causally perturb the phase of the Q64 `memory.current` staircase in the way predicted by Linux per-CPU memcg charge stock?

This follows:

- MEMCG-001: `SUPPORT_H64`
- MATH-001: `MODEL64_WINS`

The experiment tests mechanism, not only pattern.

## Kernel mechanism used for preregistration

Inspected upstream source:

`torvalds/linux@72d3fcf802c45d00b300f25b848a93c3a2bd7c7e`

Relevant facts:

- `MEMCG_CHARGE_BATCH = 64U`
- `memcg_stock` is `DEFINE_PER_CPU_ALIGNED`
- stock access uses `this_cpu_ptr(&memcg_stock)`
- `consume_stock(memcg, 1)` uses the current CPU's cached stock
- on a stock miss, `try_charge_memcg` starts with
  `batch = max(MEMCG_CHARGE_BATCH, nr_pages)`
- after a successful 64-page charge for a one-page request,
  `refill_stock(memcg, batch - nr_pages)`
  places the remaining 63 pages into the current CPU's stock

This yields a falsifiable migration prediction.

## Hosted substrate

- Ubuntu 26.04
- cgroup v2
- base page size must be 4096
- at least two usable CPUs required
- fresh transient cgroup per trial
- no MemoryHigh / MemoryMax
- no local-PC execution

## CPU hygiene

The workflow chooses two distinct CPUs, A and B, from the runner's allowed affinity set.

The transient service starts with process-level `CPUAffinity=A`.

The worker receives A and B explicitly.

Before baseline it verifies:
- current CPU is A;
- page size is 4096;
- CPU B is allowed by the enclosing cpuset by attempting and then restoring affinity during a preflight that performs no page touches.

The measured touch region is mapped but not touched before baseline.

## Trial arms

4 independent runner blocks.

Each block runs four arms in randomized order.

### FIXED_TOUCH

- CPU A for all 256 one-page touches.
- no migration.

Purpose:
verify the Q64 phase remains stationary without intervention.

### MIGRATE_TOUCH

- CPU A for steps 1..128.
- after the step128 sample, migrate to CPU B.
- CPU B for steps 129..256.

Prediction:
- pre-migration positive events form Q64;
- first post-migration positive event occurs at step129 or 130;
- later post-migration positive events are spaced 64 pages apart.

Rationale:
CPU B should not contain stock for this fresh memcg if startup and pre-intervention execution stayed on A.

### ROUNDTRIP_TOUCH

- CPU A for steps 1..128.
- CPU B for steps 129..192.
- CPU A again for steps 193..256.

Predictions:
1. first B-side positive event occurs at step129 or 130;
2. on return to A, the old A-side stock resumes;
3. the first positive event after returning to A matches the pre-migration A phase modulo64 within +/-1 page;
4. it is not required to occur immediately after returning.

This tests persistence of CPU-local hidden state.

### ROUNDTRIP_CONTROL

- identical A -> B -> A affinity interventions;
- no new anonymous pages touched.

Prediction:
no +64 accounting staircase is created by affinity syscalls/measurement alone.

## Worker

Use a dedicated C worker.

Before baseline:
- map 256-page anonymous region;
- allocate/prefault sample buffers;
- open cgroup files;
- warm fixed read/parser paths;
- remain on CPU A.

Per sample record:
- step
- arm
- current CPU
- page size
- memory.current
- memory.stat anon/kernel/pagetables
- minor faults
- migration marker

Migration procedure:
- call `sched_setaffinity` for the target CPU;
- loop with `sched_yield` until `sched_getcpu()` equals target;
- fail trial if target CPU is not reached;
- do not allocate dynamic memory during migration.

## Primary derived events

`D_n = (memory.current_n - memory.current_(n-1)) / PAGE_SIZE`

Positive charge event:
`D_n >= 16 pages`

Negative discontinuities remain recorded and are never discarded.

For each arm report:
- all non-zero D_n;
- positive-event magnitude;
- positive-event positions;
- per-regime modulo64 phase;
- CPU at every event.

## Causal metrics

### fixed_phase_error

Circular modulo64 distance between pre-128 and post-128 positive-event phases in FIXED_TOUCH.

### migration_first_charge_delay

`first_positive_step_after_128 - 128`

for MIGRATE_TOUCH and ROUNDTRIP_TOUCH.

### migrated_spacing_error

Absolute difference between successive B-side positive-event spacing and 64.

### return_phase_error

For ROUNDTRIP_TOUCH:

- infer A phase from positive events before step128;
- find first positive event after step192;
- compute circular modulo64 distance from the inferred A phase.

### control_event_count

Number of positive events in ROUNDTRIP_CONTROL.

## Preregistered decision

### SUPPORT_PERCPU_STOCK

Require at least 3/4 blocks to satisfy all available arm criteria:

FIXED_TOUCH:
- Q64 positive jumps;
- fixed_phase_error <= 1 page.

MIGRATE_TOUCH:
- first post-migration +64 event delay in {1,2};
- later B-side positive spacing = 64 +/-1 pages when a second event is present.

ROUNDTRIP_TOUCH:
- first B-side +64 event delay in {1,2};
- return_phase_error <= 1 page;
- first A-return event is consistent with the old A phase, not a forced immediate-reset rule.

ROUNDTRIP_CONTROL:
- control_event_count = 0.

Additionally:
- event CPU receipts must match A/B intervention schedule.

### REJECT_PERCPU_STOCK

If 0/4 or 1/4 blocks show the predicted migration/roundtrip response and a stable contrary pattern is observed.

### INCONCLUSIVE

Otherwise.

## Secondary model competition

Fit two causal models to intervention arms:

### GLOBAL_PHASE

One Q64 phase continues regardless of CPU identity.

### PERCPU_PHASE

Each CPU carries its own Q64 phase/state; returning to a CPU restores its previous phase unless an observed reset intervenes.

Compare:
- exact event-position prediction;
- exception count;
- MDL conditional on intervention schedule.

This is secondary to the preregistered causal criteria.

## Why this is high-information

MEMCG-001 established the quantum.
MATH-001 established predictive Q64 structure.

MEMCG-002 changes the variable named by the source implementation itself:

**current CPU identity.**

A successful intervention would link:
- source-level per-CPU stock;
- observed Q64 accounting;
- resettable phase;
- causal manipulation.

## Local replication boundary

If hosted MEMCG-002 supports the per-CPU stock model, the next substrate test may repeat the exact worker on Lubuntu through:

`MVCA -> MCP transport -> Local Desktop Commander`

That requires a separately bound local execution scope.

Hosted and local results remain separate evidence domains.

## Launch boundary

Design only.
Do not launch in this bounce.
No local-PC execution.
No memory-control policy.
