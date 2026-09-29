# MATH-015 — The 17-page latent component

> **Status:** EXISTING-EVIDENCE RESULT / NO NEW PHYSICAL RUN
> **Input:** MEMCG-005G-C v2 raw trial JSON, run 36595481746
> **Purpose:** explain the recurrent -17 memory.current emission without rewriting the frozen pilot endpoint.

## 1. Raw-sequence finding

All eight controlled-spawn block ZIPs were re-opened and all 72 trial JSON sequences were inspected.

There are 23 negative measured deltas:

- -17 pages: 20
- -13 pages: 1
- -3 pages: 1
- -2 pages: 1

The -17 events occur in both calibration and post-primer bait phases.

Representative events:

- start 116 -> calibration-14: 116 -> 99
- start 115 -> calibration-14: 115 -> 98
- start 180 -> calibration-13: 180 -> 163
- start 179 -> calibration-20: 179 -> 162
- primer-qualified bait: 178 -> 161 while terminal stock phase remains correct

Therefore -17 is not restricted to primer acquisition and does not necessarily disturb the stock-CPU terminal phase.

## 2. Start-state modes

post_migration_current_pages is strongly discrete.

Major observed islands:

- 98..100
- 114..117
- 161..163
- 179..180

A compact additive description is:

baseline mode
+ optional 17-page component
+ optional approximately-one-batch component

The physical identity of the second component is not frozen here.
Do not label it stock-CPU residual: the worker has not yet performed its first measured charge on S.

## 3. 17-page shift

For the 20 exact -17 specimens, subtracting 17 from the start-state value gives:

- exact clean-support landing: 17/20
- within 1 page of clean support: 19/20

Examples:

- 115 -> 98
- 116 -> 99
- 179 -> 162
- 180 -> 163

This supports a model in which the trial begins with an independently accounted 17-page component that can later disappear.

## 4. Pseudo hold-out

The mode structure was noticed using blocks 0..3 and checked against blocks 4..7.

Using the same additive mode family:

- blocks 0..3: 33/36 exact, 34/36 within 1 page
- blocks 4..7: 35/36 exact, 35/36 within 1 page

For held-out blocks 4..7, every exact -17 event shifts onto a clean mode:

- 180 -> 163
- 179 -> 162
- 116 -> 99
- 115 -> 98

This does not turn the post-hoc model into a preregistered result, but strongly reduces the likelihood that the lattice is a single-block visual coincidence.

## 5. Association test

Among the 69 trials within 1 page of the additive mode family:

### no 17-component class

- n = 42
- exact -17 events = 0

### 17-component class

- n = 27
- exact -17 events = 19

One-sided Fisher exact:

p ~= 4.8e-11

The association is therefore extremely strong descriptively.

Because the component classes were discovered post hoc, this p-value is not a confirmatory error-controlled claim.

## 6. Timing

Most calibration -17 events occur around measured touch 13 or 14.

Observed exact -17 positions also include:

- touch 1
- touch 11
- touch 18
- touch 20

Primer-qualified -17 bait events occur after an observed Q64 reset and still preserve the terminal b62/b63 pattern.

The timing pattern is compatible with an asynchronous lifetime process rather than a fixed stock-consumption count.

No wall-clock timestamp was recorded in v2, so this cannot yet be tested directly.

## 7. Source-constrained candidate mechanisms

Linux v7.0 provides at least two distinct ways memory.current can fall:

### A. memcg stock drain

drain_stock():

- reads stock->nr_pages[i]
- calls memcg_uncharge(old, stock_pages)
- resets the stock entry

A preparation-CPU stock drain would lower memory.current without consuming the stock-CPU S phase.

This is strongly compatible with the preserved post-primer terminal phase.

### B. ordinary folio/accounting uncharge

uncharge_folio() -> uncharge_batch() -> memcg_uncharge()

This also lowers memory.current without being a measured data-page charge.

The current v2 receipts cannot distinguish A from B.

## 8. What is rejected

### R1 — fixed folio-batch size 17

Current Linux FOLIO_BATCH_SIZE is 31, not 17.

A generic "Linux frees folios in groups of 17" explanation is unsupported.

### R2 — negative stock consumption

A negative memory.current delta is not interpreted as negative residual stock.

### R3 — stock-CPU S component from pre_current alone

Before the first measured touch on S, start-state memory.current cannot be used as a direct read of S residual stock.

## 9. Strong working hypothesis

The best current hypothesis is:

1. the worker/cgroup starts with a reproducible transient 17-page accounted component;
2. that component can be asynchronously uncharged during the measured sequence;
3. its removal produces the recurrent -17 emission;
4. the component is independent enough from S-CPU charge stock that terminal post-primer phase arithmetic remains intact.

A preparation-CPU stock residue is one concrete candidate, but is not yet proven.

## 10. Next discriminating observation

A minimal observer should trace kernel charge/uncharge paths during a short spawn-like trial.

Required signals:

- memcg_uncharge(memcg, nr_pages)
- call stack for nr_pages == 17
- refill_stock(memcg, nr_pages)
- try_charge_memcg / charge-side timing
- worker PID / CPU
- wall-clock timestamp for each user-space touch
- memory.current before/after
- VmRSS/RssAnon/RssFile/VmPTE before/after when feasible

Discriminator:

- stack through drain_stock => stock-drain explanation
- stack through uncharge_batch => ordinary folio/reclaim explanation
- another caller => new mechanism

Do not scale b63 reliability before this observation channel is cleaner.
