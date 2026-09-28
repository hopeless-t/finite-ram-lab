# MEMCG-002 CPU-Stock Causal Result v1

> **Status:** PASS / REJECT_PERCPU_STOCK (naive model) / PERCPU_PHASE REMAINS FAVORED
> **Run:** `36456299417`
> **Launch commit:** `f359c7f619e4916aef403c33156307862204395a`
> **Aggregate artifact id:** `10984859721`
> **Aggregate digest:** `sha256:161ffa1bf0b350dfad06397434c3185ca682a3e3603040265c3bc5af9772bb75`

## Validity

- 16 / 16 trials completed
- 4 runner blocks
- 4 arms per block
- Ubuntu 26.04.1 LTS
- kernel `7.0.0-1012-azure`
- systemd `259 (259.5-0ubuntu3.4)`
- cgroup v2
- 4096-byte base pages
- CPU A = 0
- CPU B = 1
- allowed CPUs = [0,1,2,3]

## Preregistered decision

`REJECT_PERCPU_STOCK`

under the intentionally strict naive model.

Full-block support:

`0 / 4`

The failed prediction was not Q64 itself. The failed prediction was the stronger assumption that each CPU would preserve a simple, durable, target-memcg-specific stock phase that became immediately visible in total `memory.current`.

## Arm-level result

### FIXED_TOUCH

`4 / 4 PASS`

CPU-fixed runs retained a stable Q64 phase.

Examples:
- block0: 32,96,160,224
- block1: 38,102,166,230
- block2: 34,98,162,226
- block3: 32,96,160,224

All positive jumps were +64 pages.

### ROUNDTRIP_CONTROL

`4 / 4 PASS`

CPU migration without page touches produced no positive accounting staircase.

Therefore affinity syscalls / measurement alone did not manufacture the Q64 signal.

### MIGRATE_TOUCH

`3 / 4 PASS`

Three blocks showed the preregistered fresh-B signature:

- first B-side +64 at step129
- second B-side +64 at step193
- exact 64-page spacing

Block0 differed:
- A: +64 at31,95
- B: next visible +64 at193
- no visible +64 at129

Thus migration strongly perturbs phase/state, but a visible immediate +64 in total `memory.current` is not guaranteed.

### ROUNDTRIP_TOUCH

`1 / 4 PASS`

block0:
- A: 35,99
- B: 129
- A return: 227
- old A phase restored exactly

blocks1/2:
- B immediate +64 at129
- A return event occurred at251 / 254 rather than old-phase 227 / 229

block3:
- B event at191 rather than129
- A return event at224 restored old A phase

Thus A-state restoration is real in some blocks but is not a durable deterministic rule under the tested shared runner conditions.

## Model comparison

Event-exception counts:

- GLOBAL_PHASE: **31**
- PERCPU_PHASE: **11**

Preferred by exceptions:

`PERCPU_PHASE`

So the strict preregistered mechanism is rejected, while CPU-conditioned phase remains substantially more predictive than a single global phase.

## Source-level correction to the naive model

Further upstream-source inspection shows that Linux does not implement one permanent target-memcg stock object per CPU.

At:

`torvalds/linux@72d3fcf802c45d00b300f25b848a93c3a2bd7c7e`

`mm/memcontrol.c` defines:

`NR_MEMCG_STOCK = 7`

and:

`struct memcg_stock_pcp`

contains seven:
- `nr_pages[]` entries
- `cached[]` memcg pointers

plus a rotating:

`drain_idx`

The source comment states that the seven cached memcgs and their page counts are sized to fit in one cache line.

When no empty slot exists, `refill_stock()` drains the slot selected by `drain_idx` and replaces it.

Therefore the better mechanism candidate is:

**a per-CPU, seven-slot shared memcg charge cache with eviction/drain, not a permanent per-CPU phase register for one memcg.**

## Why total memory.current can hide a CPU-local transition

`memory.current` observes net memcg charge.

A target-CPU 64-page charge may overlap with cached-stock uncharge/drain elsewhere in the same observation interval.

Therefore:

**absence of a +64 net jump does not prove absence of a target-CPU refill.**

This is a key measurement limitation exposed by MEMCG-002.

## Accepted conclusion

MEMCG-002 rejects the naive durable per-CPU-stock model.

It does **not** reject:
- Q64 accounting;
- CPU-conditioned hidden state;
- per-CPU stock as a mechanism family.

Instead it exposes a more specific candidate:

**Q64 behavior generated through a shared seven-slot per-CPU memcg cache whose entries can be drained or evicted.**

## Next experiment

MEMCG-003 should directly perturb slot occupancy.

Target design:
1. prime target memcg stock on one CPU;
2. hold the target process/cgroup alive;
3. run controlled distinct helper memcgs on the same CPU one at a time;
4. count how many distinct memcg insertions are needed before the target stock is visibly drained/evicted;
5. compare candidate capacities 1..10, with 7 preregistered from source;
6. include no-churn and same-memcg controls.

This tests the newly discovered seven-slot structure directly rather than inferring it from migration phase.

## Authority boundary

Hosted Linux accounting research only.
Not a DRAM hardware law.
No local-PC execution.
No memory-control policy.
