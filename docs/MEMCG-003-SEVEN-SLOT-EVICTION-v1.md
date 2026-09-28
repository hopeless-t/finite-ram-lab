# MEMCG-003 Seven-Slot Stock Eviction Probe v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Scientific question

Does the observed Q64 phase instability follow the source-level finite capacity of the per-CPU memcg stock cache?

Upstream source at:

`torvalds/linux@72d3fcf802c45d00b300f25b848a93c3a2bd7c7e`

defines:

`NR_MEMCG_STOCK = 7`

and stores seven cached memcg pointers plus seven page-count entries in each per-CPU `memcg_stock_pcp`.

When the cache is full, `refill_stock()` drains the slot selected by rotating `drain_idx` and replaces it.

MEMCG-003 tests that finite slot count directly.

## Core causal idea

Use one CPU and a sequence of persistent, distinct memcgs.

1. fill the per-CPU cache with seven controlled persistent wash memcgs;
2. start one persistent target memcg on the same CPU;
3. target insertion must evict one wash slot and occupy that slot;
4. insert one new persistent challenger memcg at a time;
5. because `drain_idx` rotates, the target slot should survive six subsequent replacements and be selected on the seventh;
6. observe the target memcg's own `memory.current` after every challenger insertion;
7. after the predicted eviction point, trigger one new target page touch and test for a fresh Q64 charge.

This converts the source-level integer **7** into a falsifiable event-count prediction.

## Hosted substrate

- Ubuntu 26.04
- cgroup v2
- page size must be 4096
- one chosen allowed CPU
- no MemoryHigh / MemoryMax
- all target/wash/challenger units pinned to the same CPU
- fresh runner block per replication
- persistent helper units remain alive until the trial is complete

## Why persistent helper memcgs are required

If a helper exits and its cgroup is destroyed, its cached stock may be drained.

Therefore wash/challenger memcgs must stay alive so their distinct memcg identities continue competing for the finite seven-slot cache.

## Worker roles

### HOLDER

Dedicated minimal C worker.

On startup:
- pin to designated CPU;
- allocate fixed buffers;
- map anonymous pages;
- warm fixed I/O paths;
- touch enough memory to establish a memcg stock entry;
- publish READY;
- then block without further memory allocation until STOP.

Used for wash and challenger memcgs.

### TARGET

Dedicated interactive C worker.

On startup:
- same low-noise preparation;
- establish target stock entry;
- publish READY;
- block on a pre-opened FIFO/event channel.

On PROBE:
1. sample own `memory.current`;
2. touch exactly one previously untouched 4 KiB page;
3. sample own `memory.current` again;
4. emit pre/post current, delta pages, minor faults.

The probe consumes at most one cached page when stock survives.

## Controlled cache initialization

### Wash phase

Launch **7 persistent wash memcgs** sequentially on the selected CPU.

Each reaches READY before the next starts.

Rationale:
seven distinct persistent memcgs are sufficient to populate all seven source-level cache slots under the idealized model, replacing unknown initial occupancy.

### Target insertion

Launch the TARGET as the next distinct memcg.

With a full cache, its insertion should evict one wash entry and occupy that exact replacement slot.

Record target `memory.current` and one baseline probe.

## Challenger phase

Launch persistent challenger memcgs C1..C8 one at a time.

After each challenger reaches READY:
- sample target `memory.current` externally;
- send one PROBE to target;
- record target pre/post touch current.

Predicted source-level behavior under a clean seven-slot rotation:

- after C1..C6: target stock survives;
- at C7: target slot is selected for drain/eviction;
- target pre-probe `memory.current` drops by its remaining cached-stock charge;
- target probe after C7 produces a fresh +64-page charge;
- C8 behavior occurs after target reinsertion and is reported but is not part of the primary threshold decision.

## Controls

### SAME_MEMCG_ACTIVITY

Instead of distinct challengers, repeatedly command one already-existing helper memcg to touch more pages.

Prediction:
no target slot eviction merely from repeated activity in the same competing memcg identity.

### SIX_ONLY

Stop after six distinct challenger insertions.

Prediction:
target stock is still resident.

### NO_CHURN

Keep target idle for an equivalent wall-clock interval.

Prediction:
no stock-eviction signature absent cache churn.

## Primary measurements

For target after each challenger count m:

- external target `memory.current`
- target probe pre-current
- target probe post-current
- probe delta pages
- target minor faults
- challenger count
- exact unit/cgroup identities
- CPU receipt

Derived:

`stock_drop_pages(m) = pre_current(m-1) - pre_current(m)`

when positive.

Fresh-charge event:

`probe_delta_pages >= 16`

Expected fresh-charge magnitude:

`~64 pages`

## Primary integer-capacity inference

For each block define:

`E = first challenger count where target shows eviction/fresh-recharge evidence`

Candidate capacities:

`K in {1,2,3,4,5,6,7,8,9,10}`

Source preregistration:

`K = 7`

## Mathematical analysis

### 1. Threshold likelihood

Treat each block as a censored discrete threshold observation.

Compare candidate K by:
- exact-match count;
- absolute threshold error;
- leave-one-block-out prediction.

### 2. MDL

Encode challenger survival sequence as:

`1111110...`

where 1 = stock survives and 0 = eviction detected.

Compare:
- fixed-K threshold model;
- arbitrary binary sequence;
- geometric/no-memory model.

### 3. Bayesian discrete model

Use a simple categorical prior over K=1..10.

Update from block thresholds using a one-step jitter model:
- exact K probability mass highest;
- +/-1 allowed lower likelihood;
- farther thresholds strongly penalized.

Report posterior over K without treating it as a hardware constant.

### 4. Counterexample search

Report:
- early eviction (<7)
- late survival (>7)
- spontaneous no-churn eviction
- same-memcg control eviction

These are scientifically valuable and must not be discarded.

## Preregistered decision

### SUPPORT_K7_SLOT_MODEL

Require:
- at least 3/4 blocks with E in {6,7,8};
- modal E = 7;
- median E = 7;
- SAME_MEMCG_ACTIVITY and NO_CHURN controls show no matching eviction threshold;
- fresh recharge after eviction is Q64-like.

### REJECT_K7_SLOT_MODEL

If 0/4 or 1/4 blocks are within {6,7,8} and a stable alternative K or non-threshold pattern is observed.

### INCONCLUSIVE

Otherwise.

## Important interpretation boundary

Even a SUPPORT_K7_SLOT_MODEL result would establish a Linux memcg accounting-cache behavior on the tested substrate.

It would not be a DRAM-cell or memory-controller hardware law.

## Local replication

Only after hosted evidence:
repeat the exact experiment on Lubuntu through MVCA -> LDC under a separately bound local execution scope.

## Launch boundary

Design only.
No hosted launch in this bounce.
No local-PC execution.
No memory-control policy.
