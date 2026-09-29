# MEMCG-004 Calibrated Stock State v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Motivation

MEMCG-003B established that merely creating a persistent memcg worker does not guarantee a known stock state.

Relevant upstream behavior:

- `consume_stock()` removes the cached memcg pointer when stock reaches zero.
- `refill_stock()` can add pages to an existing entry.
- if an existing entry grows beyond `MEMCG_CHARGE_BATCH`, the slot is drained.
- kernel-memory and socket uncharges can also feed `refill_stock()`.

Therefore worker startup and runtime charge/uncharge activity can alter slot occupancy and residual stock before a seven-slot experiment begins.

The next atomic question is not yet "is K=7?".

It is:

**Can the experiment create and verify a known, stable 63-page memcg stock state?**

## Core calibration principle

For a one-page request on a stock miss:

- Linux charges a 64-page batch;
- one page satisfies the request;
- the remaining 63 pages are refilled into the current CPU's stock.

Therefore stop immediately after directly observing a fresh +64-page `memory.current` jump.

At that instant the model predicts approximately 63 pages of consumable stock.

## Substrate

- Ubuntu 26.04 hosted runner
- cgroup v2
- 4096-byte base page
- at least two allowed CPUs
- control/orchestration pinned to CPU C
- worker pinned to distinct stock CPU S
- no MemoryHigh / MemoryMax
- fresh transient cgroup per trial

## Worker requirements

Use a dedicated interactive C worker derived from the proven MEMCG-001 low-noise design.

Before calibration:
- pin to S;
- map and reserve at least 256 anonymous pages;
- preallocate/prefault all measurement/control buffers;
- open control channel;
- perform no measured-page touches;
- enter command loop.

Commands must not allocate dynamic memory.

### TOUCH_ONE

Touch exactly one previously untouched 4 KiB page and acknowledge with a fixed preallocated path.

### STOP

Exit cleanly.

## External measurement

The controller runs only on C.

For each TOUCH_ONE:
1. read target `memory.current`;
2. command one target page touch;
3. wait for deterministic acknowledgement;
4. read target `memory.current` again;
5. compute delta pages.

Calibration event:

`60 <= delta_pages <= 68`

Stop calibration touches immediately at the first such event.

Record:
- touch index of calibration event;
- exact delta;
- target current before/after;
- CPU receipts;
- minor-fault count.

## Hold test

After the calibration +64 event:

- target performs zero touches;
- controller performs 64 passive samples over a fixed hold window;
- target cgroup receives no intentional competitor memcg.

Primary hold criterion:

- no passive drop >=16 pages.

This tests whether the calibrated stock survives long enough to be a usable experimental initial state.

## Consumption validation

After hold:

issue exactly 64 TOUCH_ONE commands, measuring target current after each.

Prediction if residual stock really equals 63 pages:

- validation touches 1..63: no new +64 charge;
- validation touch 64: fresh +64-page charge.

Allow +/-1 page event magnitude tolerance as in prior Q64 work.

Primary derived value:

`R = number of post-calibration touches before next fresh Q64 charge`

Source prediction:

`R = 64`

where the fresh charge occurs on the 64th validation touch.

## Blocks and controls

4 independent hosted blocks.

Each block runs:

### CALIBRATED

Prime to first observed +64, hold, then 64-touch consumption validation.

### NO_HOLD

Prime to +64 and immediately run consumption validation.

Purpose:
separate hold-time loss from calibration error.

### CONTROL_NO_PRIME

Run the same passive hold and validation schedule without conditioning on a fresh +64 calibration event.

Purpose:
show that the exact R=64 phase depends on calibrated initialization rather than arbitrary startup phase.

## Preregistered decision

### SUPPORT_CALIBRATED_STOCK

Require at least 3/4 CALIBRATED blocks:

- a fresh calibration event is observed;
- calibration magnitude in [60,68] pages;
- hold has no passive drop >=16 pages;
- next fresh Q64 event occurs on validation touch 64 +/-1.

Additionally:
- NO_HOLD must not perform worse than CALIBRATED in a way suggesting the hold observer itself creates the state;
- CONTROL_NO_PRIME must not reproduce exact calibrated phase in all blocks.

### REJECT_CALIBRATED_STOCK

If 0/4 or 1/4 CALIBRATED blocks show the predicted residual-stock phase and a stable alternative is observed.

### INCONCLUSIVE

Otherwise.

## Mathematical analysis

Candidate residual stock phase:

`R in 1..128`

Report:
- absolute error to R=64;
- exact-match count;
- leave-one-block-out predicted R;
- MDL for fixed-phase vs arbitrary event location;
- event magnitude distribution.

This is a calibration experiment, not yet a seven-slot-capacity experiment.

## Next stage if supported

Only if MEMCG-004 supports deterministic calibrated stock:

MEMCG-005 may build:
- 7 calibrated wash entries;
- 1 calibrated target entry;
- calibrated distinct challengers;

and retest the source-level seven-slot replacement cycle.

This avoids compounding an unknown initial-state assumption into the K7 experiment.

## MATH-002 relation

MATH-002 is secondary analysis of MEMCG-003B and cannot affect MEMCG-004's preregistered design.

## Authority boundary

Hosted Linux accounting research only.
No local-PC execution.
No memory-control policy.
