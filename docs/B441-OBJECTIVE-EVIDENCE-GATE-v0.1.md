# B441 — Objective Evidence Gate v0.1

Status: **evidence-gating rule validated against historical STRATA-005 replay**. No new physical experiment ran.

## 1. Problem

B440 showed that a measured Pareto transition can appear or disappear depending on which observed coordinates are admitted into the objective vector.

For STRATA-005:

- pressure-oriented objectives alone show no frontier loss;
- adding scan timing creates an apparent loss of the DONTNEED-80 arm.

The original study had already classified hosted scan timing as noisy and descriptive.

A dynamic frontier framework therefore needs an evidence gate before it needs more optimization logic.

## 2. Objective evidence roles

Every measured objective must be assigned one role before frontier inference.

### PRIMARY

Pre-specified and sufficiently reliable to carry the scientific decision.

### DESCRIPTIVE

Recorded for exploration and sensitivity analysis, but not authorized to create the primary claim.

### EXCLUDED

Unavailable, contaminated, semantically incomparable, or otherwise out of scope.

Missing coordinates are never imputed as zero.

## 3. Gate order

1. Require at least one PRIMARY objective.
2. Verify every PRIMARY objective exists for the compared observation sets.
3. If a PRIMARY coordinate is missing -> INSTRUMENTATION_HOLD.
4. Compute the primary projected frontier.
5. Add available DESCRIPTIVE coordinates only in a separate sensitivity projection.
6. Never add EXCLUDED coordinates.
7. Compare lost frontier identities across projections.

## 4. Frozen classifications

### NO_MEASURED_MONOTONICITY_VIOLATION

No loss appears in the primary or descriptive extension.

### PROJECTION_FRAGILE

No frontier loss exists under PRIMARY objectives, but a loss appears after adding DESCRIPTIVE objectives.

This blocks promotion of the descriptive-only transition.

### PRIMARY_VIOLATION_STABLE_TO_DESCRIPTIVE_EXTENSION

A primary loss exists and the same lost-plan set survives the descriptive extension.

This is stronger evidence, though still not a causal diagnosis.

### PRIMARY_VIOLATION_PROJECTION_SENSITIVE

A primary loss exists, but adding descriptive dimensions changes which plans are lost.

The dynamic claim remains sensitive to objective selection.

### PRIMARY_OBJECTIVE_MISSING

Required primary evidence is unavailable.

Fail closed.

## 5. STRATA-005 application

Frozen evidence roles:

PRIMARY:

- peak_ram_bytes
- memory_high_events
- pgscan

DESCRIPTIVE:

- scan_elapsed_ns

The primary projection gives:

H=144 frontier:
- dontneed_48m

H=176 frontier:
- dontneed_48m

No primary loss.

The descriptive extension gives:

H=144:
- dontneed_48m
- dontneed_64m
- dontneed_80m

H=176:
- dontneed_48m
- dontneed_64m

So dontneed_80m disappears only after adding scan timing.

Gate result:

**PROJECTION_FRAGILE**

This matches the original experiment's frozen timing boundary.

## 6. Historical search boundary

STRATA-006 was examined as a possible stronger historical pair.

It is not a valid B439 capacity-only pair.

STRATA-006 holds MemoryHigh fixed and changes hot anonymous live state.

That is an excellent causal experiment for live-set headroom, but it changes the workload/live-state requirement rather than only expanding capacity.

Therefore it must remain a separate mechanism study.

No stronger existing primary-projection capacity pair has been identified yet.

## 7. Why this matters beyond timing

The same issue applies to many later metrics.

Examples:

- approximate energy counters;
- noisy wall-clock timing;
- derived quality estimates;
- page-cache residency sampled after a perturbing observer;
- missing GPU traffic estimates.

A Pareto framework makes every added coordinate powerful.

The evidence gate prevents weak coordinates from silently acquiring primary authority merely because they alter dominance.

## 8. Implementation

Frozen branch:

- research/objective-evidence-gate-b441

Files:

- src/finite_ram_lab/objective_evidence_gate.py
- tests/test_objective_evidence_gate.py
- specs/OBJECTIVE-EVIDENCE-GATE-v0.1.json
- docs/B441-OBJECTIVE-EVIDENCE-GATE-v0.1.md

## 9. New principle H441 — Evidence precedes dimension

> An objective coordinate should enter the primary Pareto space only after its measurement semantics and evidence authority are frozen.

The number of measurable metrics should not determine the number of primary objectives.

## 10. Next step

The STRATA-005 block artifacts are still available.

B442 should use the original four independent blocks to estimate **frontier membership stability under resampling**.

This provides an orthogonal guard:

- Evidence role asks whether a coordinate is authorized.
- Resampling stability asks whether the observed frontier relation is statistically stable even within that role.

A descriptive-only and resampling-unstable transition should remain strictly exploratory.
