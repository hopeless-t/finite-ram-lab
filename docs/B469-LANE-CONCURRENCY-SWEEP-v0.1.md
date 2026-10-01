# B469 — Residue Lane Concurrency Sweep v0.1

Status: **HOSTED NUMERICAL COARSE FRONTIER**.

## 1. Goal

B468 selected residue-lane concurrency because the measured representation
residency effect was about 682x larger than the largest tested tile-row median
peak effect.

B469 physically sweeps the new axis.

## 2. Definition of q

`q` is the maximum number of residue result matrices intentionally retained
before they are folded into the exact CRT accumulator and released.

Total residue lane count remains seven.

```text
q=1
produce one lane
-> fold
-> release

q=2
produce two lanes
-> fold both
-> release group

q=4
produce four lanes
-> fold group
-> release
-> remaining group

q=7
produce all seven lanes
-> fold all
-> release
```

Thus q interpolates between streamed and all-resident representation schedules.

## 3. Frozen logical residency

For the 2048x2048 result surface:

- int64 accumulator = 32 MiB;
- each uint8 residue lane = 4 MiB.

Expected logical simultaneous live bytes:

```text
q=1 -> 36 MiB
q=2 -> 40 MiB
q=4 -> 48 MiB
q=7 -> 60 MiB
```

These are model bytes, not asserted VmHWM values.

## 4. Balanced execution

Four repetitions are used.

Orders:

```text
1,2,4,7
7,4,2,1
2,1,7,4
4,7,1,2
```

Every q occupies every execution position exactly once.

Every observation runs in a fresh process.

## 5. Hard gates

Every child must:

- reconstruct the exact integer result;
- share one final output SHA256 across all q;
- use seven total residue lanes;
- use tile_rows=64;
- use the same seed and value range.

A semantic mismatch blocks frontier interpretation.

## 6. Endpoints

For each q:

- median normalized VmHWM growth;
- min/max normalized peak;
- median work time;
- min/max work time;
- logical live bytes.

Relative to q=1:

- peak delta;
- latency ratio.

B469 also computes the exact observed two-objective Pareto set over:

- lower median peak;
- lower median work time.

No arbitrary weighted score is used.

## 7. Research question

The important shape is not merely whether memory rises with q.

It is whether extra resident lanes buy enough latency reduction to justify their
peak cost.

That is the first direct KMEP/FROP-like operating surface in this lane.

## 8. Claim ceiling

**HOSTED_NUMPY_GROUPED_RESIDUE_CONCURRENCY_SWEEP**

The observed q frontier belongs to this implementation and hosted environment.

## 9. Next

If the coarse q surface shows a clear tradeoff, B470 should localize the useful
region and define a governor rule using constraints/Pareto dominance rather than
one universal q.
