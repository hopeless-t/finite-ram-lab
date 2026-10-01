# B440 — STRATA-005 Historical Dynamic Replay v0.1

Status: **historical aggregate reanalysis**. No new physical run was executed.

## 1. Why this is the first real B439 input

B439 was designed to compare the same plan identity across two capacities.

STRATA-005 already provides exactly that experimental structure:

- same hosted runner/workload family;
- same 64 MiB hot anonymous allocation;
- same 96 MiB cold file;
- same read chunk;
- same DONTNEED implementation;
- same named arms;
- only MemoryHigh changed between the new study points.

The two frozen capacities are:

- MemoryHigh = 144 MiB
- MemoryHigh = 176 MiB

The original artifact remains valid and unmodified.

## 2. Recovered source artifact

Workflow run:

- 36431449193

Artifact:

- id 10973632531
- STRATA-005-EXTERNAL-VALIDITY-36431449193
- sha256:8702206b4cb645796f0c2ca17f60bc155898d380225f6216804b790396592554
- 40 / 40 trials
- execution PASS

B440 re-downloaded the frozen artifact and read its aggregate summary.

No trial was rerun.

## 3. Objective projection

The original aggregate exposes medians for:

- maximum scan memory.current
- MemoryHigh events
- pgscan
- scan elapsed
- post-scan memory
- file residency
- other descriptive metrics

B440 intentionally does **not** fabricate missing byte-seconds, transfer bytes, or error coordinates.

Instead it introduces a projected-observation comparator that operates only on explicitly named observed dimensions.

## 4. Primary pressure projection

Primary projection:

- peak RAM
- MemoryHigh events
- pgscan

At MemoryHigh=144 MiB the exact projected frontier is:

- DONTNEED 48 MiB

At MemoryHigh=176 MiB the exact projected frontier is also:

- DONTNEED 48 MiB

Therefore:

- lost frontier IDs: none
- measured monotonicity violation: none

Under the pressure-oriented projection, STRATA-005 does **not** provide a B438 monotonicity-violation example.

## 5. Extended timing projection

Add:

- scan elapsed time

to the same minimization vector.

Then at MemoryHigh=144 MiB the projected frontier becomes:

- DONTNEED 48 MiB
- DONTNEED 64 MiB
- DONTNEED 80 MiB

At MemoryHigh=176 MiB:

- DONTNEED 48 MiB
- DONTNEED 64 MiB

So DONTNEED 80 MiB disappears.

## 6. Why DONTNEED 80 disappears under the timing projection

Observed median changes for the same DONTNEED-80 plan from H=144 to H=176:

- peak RAM: +15,458,304 bytes
- MemoryHigh events: -7
- pgscan: -4096
- scan elapsed: +20,712,903.5 ns

So the plan improves on the pressure-event/reclaim coordinates but worsens on peak RAM and elapsed time.

The DONTNEED-64 plan also changes:

- peak RAM: +131,072 bytes
- scan elapsed: -37,249,712.5 ns

At H=176, DONTNEED 64 is no worse than DONTNEED 80 on every selected coordinate and is strictly better on peak RAM and elapsed time.

Therefore B440 classifies the loss as:

**LOST_WITH_SELF_AND_DOMINATOR_COST_SHIFT**

This refines the B439 classifier, which originally treated self and dominator changes as mutually exclusive explanation paths.

## 7. Why this is not strong evidence of a dynamic frontier reversal

The original STRATA-005 result explicitly froze this evidence boundary:

> hosted scan timing remains noisy and non-monotonic; timing is descriptive only and is not used to choose cadence.

That boundary remains authoritative.

The B440 apparent frontier loss occurs **only** when that descriptive timing coordinate is admitted.

If timing is removed, the frontier loss disappears.

Therefore the correct conclusion is not:

> Increasing MemoryHigh caused DONTNEED 80 to become dynamically inferior.

The correct conclusion is:

> The B439 comparator can ingest a real historical capacity pair, and the apparent monotonicity signal is sensitive to an objective that the original experiment already classified as noisy.

This is a successful replay and a negative robustness result.

## 8. New lesson: objective projection is part of evidence quality

A Pareto frontier is always relative to the chosen objective coordinates.

Adding a noisy coordinate can turn a dominated plan into a frontier plan.

If that coordinate then changes across capacities, an apparent frontier disappearance can be created.

Therefore a dynamic frontier claim requires not only stable plan identity and capacity control, but also an **evidence-qualified objective projection**.

## 9. Proposed evidence classes

B440 motivates three objective roles.

### PRIMARY

Pre-specified and sufficiently reliable for the scientific decision.

For STRATA-005:

- MemoryHigh event behavior
- scan memory peak / pressure-related memory observations
- pgscan/pgsteal where defined by the frozen design

### DESCRIPTIVE

Recorded and useful for exploration, but not authorized for primary inference.

For STRATA-005:

- hosted scan timing / throughput

### EXCLUDED_OR_UNKNOWN

Unavailable, contaminated, or not semantically comparable.

These coordinates must not be filled with zero.

## 10. Implementation

Frozen on branch:

- research/historical-dynamic-replay-b440

Files:

- src/finite_ram_lab/historical_dynamic_replay.py
- tests/test_historical_dynamic_replay.py
- analysis/inputs/B440-STRATA005-HISTORICAL-DYNAMIC-REPLAY-v0.1.json
- docs/B440-STRATA005-HISTORICAL-DYNAMIC-REPLAY-v0.1.md

The projected comparator supports:

- arbitrary explicit objective names;
- stable plan IDs;
- projected Pareto frontiers;
- objective deltas;
- self-shift detection;
- dominator-shift detection;
- combined self+dominator shift;
- missing/new-plan distinctions.

## 11. Validation performed in this bounce

The frozen artifact was independently re-read.

Direct recomputation from its summary gives:

Primary pressure projection:

- H=144: {dontneed_48m}
- H=176: {dontneed_48m}

Extended timing projection:

- H=144: {dontneed_48m, dontneed_64m, dontneed_80m}
- H=176: {dontneed_48m, dontneed_64m}

No new physical experiment was run.

## 12. New hypothesis H440 — Projection Fragility

> A measured Pareto transition should not be promoted as a physical frontier effect when it disappears after removing objective coordinates that were pre-classified as descriptive/noisy.

This gives a concrete guardrail for B439.

## 13. Next bounce B441

Formalize an **Objective Evidence Gate**.

Before a measured frontier can support a dynamic monotonicity claim:

1. each objective receives PRIMARY / DESCRIPTIVE / EXCLUDED status;
2. the primary projection is evaluated first;
3. descriptive coordinates are added only as sensitivity analyses;
4. any frontier-loss result that exists only in descriptive projections is marked PROJECTION_FRAGILE;
5. missing objectives remain missing.

Then search the existing historical corpus for a stronger real pair where a primary projection itself changes.
