# MEMCG-005D External-Migration First-Touch v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

Does the worker's own migration path account for the zero-delta first-touch failures that persisted in MEMCG-005C?

MEMCG-005C rejected the receipt-I/O hypothesis.

MEMCG-005D removes both post-migration receipt I/O **and** the worker's own `sched_setaffinity()` syscall from one arm.

## CPU roles

Require at least three allowed CPUs:

- C = controller
- P = preparation/spin CPU
- S = stock-test CPU

Controller pinned to C.

Every worker starts on P.

## Shared-latch worker

Each fresh worker receives a dedicated one-page shared control mapping.

Before READY-equivalent state:

- open/map the shared page on P;
- prefault it on P;
- map measured anonymous pages but do not touch them;
- initialize shared fields;
- write `READY=1`;
- enter a tight userspace spin loop reading only the prefaulted shared page.

No FIFO/status write is permitted after READY and before the measured touch.

Shared fields:

- READY
- GO
- DONE
- STOP
- OBSERVED_CPU
- TOUCHED

Use atomics / volatile ordering sufficient for this single-producer/single-consumer protocol.

## PID discovery

The controller obtains the worker MainPID externally through systemd metadata.

The worker does not emit a PID/status receipt after entering the spin state.

## Arms

Four independent hosted blocks.

Each block uses 23 fresh identities per arm.

### SELF_ATOMIC

Worker remains on P until GO.

Controller:
1. samples pre `memory.current`;
2. writes GO with target CPU S.

Worker:
1. observes GO while on P;
2. calls `sched_setaffinity(0, ..., S)`;
3. confirms current CPU S without status I/O;
4. immediately touches one measured anonymous page;
5. writes DONE and OBSERVED_CPU to the prefaulted shared page.

Controller:
6. waits for DONE;
7. samples post `memory.current`.

No receipt I/O occurs before the measured touch.

### EXTERNAL_ATOMIC

Worker spins on P.

Controller:
1. samples pre `memory.current`;
2. calls `os.sched_setaffinity(worker_pid, {S})` from C;
3. externally confirms the worker has run on S using proc/scheduler metadata;
4. writes GO.

Worker:
5. observes GO while running on S;
6. performs **no migration syscall**;
7. immediately touches one measured anonymous page;
8. writes DONE and OBSERVED_CPU to the prefaulted shared page.

Controller:
9. waits for DONE;
10. samples post `memory.current`.

The worker performs no intentional syscall, allocation, status I/O, or new page fault between GO observation and the measured page touch.

## Probe count

`23 identities x 2 arms x 4 blocks = 184 first-touch probes`

This matches MEMCG-005C's scale.

## Outcome

For each identity:

`Q64_PASS = 60 <= delta_pages <= 68`

Preserve exact deltas.

Report by arm/block:

- Q64 success count;
- zero-delta count;
- other-delta count;
- ordered delta sequence;
- observed CPU receipt from shared memory.

## Primary decision

### SUPPORT_EXTERNAL_PATH

Require:

- EXTERNAL_ATOMIC Q64 success >= 90 / 92;
- at least 3/4 EXTERNAL_ATOMIC blocks have 23/23 Q64;
- EXTERNAL_ATOMIC has fewer failures than SELF_ATOMIC overall;
- no observed-CPU mismatch.

### REJECT_EXTERNAL_PATH

If EXTERNAL_ATOMIC has >=8 / 92 failures or a stable zero-delta pattern comparable to SELF_ATOMIC.

### INCONCLUSIVE

Otherwise.

## Analysis

Report:

- Clopper-Pearson interval for each arm;
- paired block failure-rate differences;
- one-sided sign test for EXTERNAL improvement;
- exact 2x2 paired outcome table by block/identity as a secondary diagnostic.

No slot-capacity inference is allowed.

## Interpretation

If SUPPORT_EXTERNAL_PATH:

the target worker's self-migration path is strongly implicated in first-touch contamination; successor K7 experiments should use controller-driven external migration plus shared-latch touch.

If REJECT_EXTERNAL_PATH:

even externally staged migration does not guarantee an empty S-side stock state, implying the problem lies below the status/migration command protocol or in independent memcg stock activity.

## Launch boundary

Design only.
Do not implement or launch in this bounce.
No local-PC execution.
No memory-control policy.
