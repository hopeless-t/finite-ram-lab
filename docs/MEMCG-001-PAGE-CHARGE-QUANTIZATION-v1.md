# MEMCG-001 Page-Charge Quantization Probe v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Scientific question

Does cgroup-v2 `memory.current` expose a reproducible discrete charge-batching structure during one-page-at-a-time anonymous allocation?

A concrete mechanism candidate is Linux memcg's 64-page charge batch.

Current upstream source snapshot inspected during design:

- `torvalds/linux@72d3fcf802c45d00b300f25b848a93c3a2bd7c7e`
- `include/linux/memcontrol.h`
- `#define MEMCG_CHARGE_BATCH 64U`

The same source tree's cgroup selftest states that memcg charging is performed using per-CPU batches 64 pages large.

On a 4096-byte base-page system:

`64 * 4096 = 262144 bytes = 256 KiB`

This numerical match motivates the experiment but is not treated as proof.

## Competing hypotheses

### H64 / charge-batch quantization

After baseline correction, `memory.current` should show a staircase-like response:

- large positive jumps near 64 base pages;
- plateau/jump spacing near 64 touched pages after the first residual-stock-dependent transition;
- a stable lattice width near 64 pages across independent blocks.

The first jump phase is not fixed because process startup may consume some per-CPU stock before the measurement baseline.

### Hpage / near-page-linear accounting

`memory.current` tracks touched pages approximately one page at a time, with no reproducible 64-page step/spacing.

### Hnoise / observer-runtime noise

Apparent jumps occur in both touch and no-touch control trials or fail to replicate in magnitude/spacing.

## Hosted substrate

- GitHub Actions `ubuntu-26.04`
- fresh transient systemd service for every trial
- cgroup v2 required
- base page size must equal 4096 bytes for v1; otherwise INVALID / redesign
- exact kernel/systemd/image/cpu receipt recorded

No MemoryHigh or MemoryMax is configured: this is accounting behavior, not pressure behavior.

## Worker design

Use a small C worker, not Python, to minimize allocator/runtime noise.

Before baseline the worker:

1. discovers its own cgroup path;
2. opens `memory.current` and `memory.stat`;
3. allocates the full anonymous target mapping;
4. allocates and prefaults its sample buffer;
5. pins itself to its current CPU with `sched_setaffinity`;
6. prefaults all fixed parsing/output buffers.

Only then is baseline captured.

### Touch mode

For steps 1..256:

1. write one byte to the next 4 KiB page;
2. sample `memory.current`;
3. sample selected `memory.stat` fields;
4. sample minor-fault count;
5. store into the already-prefaulted sample array.

256 pages = 1 MiB and spans four candidate 64-page intervals.

### Control mode

Run the identical 256-sample loop without touching new anonymous pages.

This estimates cgroup-read / runtime drift from the measurement loop itself.

## Trial matrix

4 independent hosted runner blocks.

Each block runs in randomized order:

- touch
- control

Each trial gets a fresh transient cgroup.

Total:

`4 blocks * 2 modes = 8 trials`

## Raw sample schema

Per step:

- block
- mode
- step
- pinned_cpu
- page_size
- memory_current_bytes
- memory_stat_anon_bytes
- memory_stat_kernel_bytes
- memory_stat_pagetables_bytes
- minor_faults

Step 0 is the baseline.

## Mathematical analysis

For each trial define:

`U_n = (memory.current_n - memory.current_0) / PAGE_SIZE`

and first difference:

`D_n = U_n - U_(n-1)`

### 1. Jump distribution

Record all non-zero `D_n`.

Report:

- histogram in pages;
- median positive jump;
- maximum jump;
- count of jumps >= 16 pages.

### 2. Integer-lattice / quantum search

Candidate quanta:

`Q = {1, 2, 4, 8, 16, 32, 64, 128} pages`

For each Q, score significant positive jump magnitudes by distance to the nearest integer multiple of Q.

Report the best-fitting Q without forcing Q=64.

### 3. Jump-position periodicity

For significant jumps, search phase `phi in [0,Q-1]` that maximizes jump-position concentration modulo Q.

The phase is free; only spacing is tested.

### 4. Change-point / spacing analysis

Compute spacing between successive significant jump positions.

For H64 support, repeated spacing near 64 pages should appear after the first transition.

### 5. Autocorrelation

Compute autocorrelation of the absolute first-difference sequence at lags:

`1,2,4,8,16,32,64,128`

Lag 64 is preregistered but compared against all candidates.

### 6. Control subtraction

Any quantum/periodicity appearing similarly in no-touch controls is treated as observer/runtime contamination rather than anonymous-page charge structure.

## Pre-registered directional decision

### SUPPORT_H64

Only if at least 3/4 touch blocks satisfy both:

- at least two significant positive jumps;
- median significant-jump magnitude in [60,68] pages;
- median successive jump spacing in [62,66] touched pages;

and the no-touch controls do not reproduce the same pattern.

### REJECT_H64

If 0/4 or 1/4 touch blocks satisfy the above while a different structure or near-page-linear behavior is consistently observed.

### INCONCLUSIVE

Otherwise.

The generic lattice search is reported regardless of the H64 decision.

## SQL integration

MEMCG-001 aggregate output must include a row-oriented sample table suitable for EVIDENCE-002:

- trial metadata
- step samples
- first differences
- candidate-quantum scores
- jump positions
- control comparison

The purpose is explicit counterexample search, not only confirmation.

## Local replication boundary

If hosted MEMCG-001 supports a reproducible structure, a later LOCAL-MEMCG replication may run on the user's Lubuntu machine through:

`MVCA -> MCP transport -> Local Desktop Commander`

That local run requires its own fixed execution scope and MVCA approval/binding.

Hosted and local evidence must remain separate substrate labels.

## Authority boundary

Design only.
No hosted launch in this bounce.
No local-PC execution.
No memory policy authorized.
