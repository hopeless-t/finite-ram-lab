# B439 — Static-vs-Dynamic Frontier Comparator v0.1

Status: **software comparator with synthetic dynamic examples**. No physical measurements were ingested in this bounce.

## 1. Purpose

B438 proves a static monotonicity result:

when capacity only increases and every constrained memory coordinate remains part of the Pareto objective, an old static Pareto plan cannot disappear.

B439 turns a violation of that theorem into a diagnostic signal.

Given measured plan vectors at two capacities, the comparator asks:

> If a previously Pareto-relevant plan disappeared, what changed?

## 2. Observation schema

Each measured plan has a stable plan identity and an observed vector containing:

- resident RAM
- resident VRAM
- RAM byte-seconds
- VRAM byte-seconds
- traffic
- compute
- latency
- error

The exact set of memory tiers can be extended.

Stable plan identity is essential.

Without it, a change in implementation or plan semantics can be mistaken for a capacity-dependent cost shift.

## 3. Comparator pipeline

For the smaller-capacity observation set:

1. compute the measured Pareto frontier.

For the larger-capacity observation set:

2. compute the measured Pareto frontier.

Then:

3. identify plan IDs lost from the frontier;
4. identify newly added plan IDs;
5. for each lost plan:
   - compare its own objective coordinates across capacities;
   - identify plans that dominate it at the larger capacity;
   - compare those dominators across capacities when the earlier observation exists;
   - classify the violation.

## 4. Explanation classes

### LOST_WITH_SELF_COST_SHIFT

The lost plan itself changed measured objective coordinates.

Example:

- same resident RAM/VRAM;
- latency changes from 1 to 3.

If another plan now dominates it, the loss is directly associated with the plan's own capacity-dependent runtime behavior.

Possible physical causes include:

- reclaim;
- cache behavior;
- migration;
- different page residency;
- frequency/power behavior;
- changed batching.

The comparator does not infer which cause applies. It only localizes the changed coordinates.

### LOST_WITH_DOMINATOR_COST_SHIFT

The lost plan stayed stable, but a plan that now dominates it improved.

Example:

- p latency remains 2;
- q latency changes from 3 to 1;
- RAM/VRAM coordinates stay equal.

This is the mirror image of the first case.

### LOST_WITH_NEW_OR_PREVIOUSLY_UNOBSERVED_DOMINATOR

A newly observed plan dominates the lost plan, but no same-plan observation exists at the smaller capacity.

This must not be called a runtime cost shift without additional evidence.

Possible explanations include:

- candidate set changed;
- instrumentation did not observe the plan earlier;
- plan identity changed;
- a conditional execution path became available.

### MISSING_LARGER_OBSERVATION

A previously frontier-visible plan has no corresponding larger-capacity observation.

This is an observation gap, not evidence that the plan became non-Pareto.

### UNEXPLAINED_STATIC_MONOTONICITY_VIOLATION

A plan disappears despite:

- the same plan being observed at both capacities;
- no measured change in its objective vector;
- no measured change in known dominators;
- no new/unobserved dominator.

This should be treated as an instrumentation/classification inconsistency until resolved.

## 5. Synthetic self-cost example

At smaller capacity:

- plan p: RAM=8, VRAM=4, latency=1
- plan q: RAM=8, VRAM=4, latency=2

p dominates q.

At larger capacity:

- p latency becomes 3
- q remains 2

q now dominates p.

The comparator returns:

- lost plan: p
- dominator: q
- class: LOST_WITH_SELF_COST_SHIFT
- changed coordinate: latency +2.

This is the basic shape expected when the same plan's runtime behavior changes with capacity.

## 6. Synthetic dominator-shift example

At smaller capacity:

- p latency=2
- q latency=3

At larger capacity:

- p remains 2
- q improves to 1.

p disappears from the frontier.

The comparator returns:

- lost plan: p
- dominator: q
- class: LOST_WITH_DOMINATOR_COST_SHIFT
- q changed coordinate: latency -2.

## 7. Why this connects the theory to physical experiments

The Live-State Frontier research now has two independent evidence layers.

### Static layer

B426-B438:

- semantic release proofs
- ownership
- representation
- temporalization
- placement
- tier capacities
- activation antichains
- monotone static phase diagram.

### Dynamic layer

Existing and future physical work:

- memcg stock behavior
- pressure knees
- reclaim
- page residency
- GPU migration
- expert cache hit rates
- observed transfer time
- measured latency.

B439 is the bridge.

It does not merge the evidence.

It compares them.

## 8. Relationship to the B425 ambient catcher

B425 remains paused and has not run.

If it runs later, its receipts can eventually provide dynamic observations such as:

- stock-state transition
- owner refill/uncharge
- boundary touch
- ambient Q64 reset
- probe health.

Those observations should not be forced into the optimizer directly.

Instead, they can be used to estimate whether objective coordinates or pressure state changed between capacity conditions.

B439 can then test whether the measured frontier violates the static expectation.

## 9. Relationship to GPU/Strata measurements

A future Strata capacity experiment could hold a plan identity fixed while varying a controlled capacity or residency budget.

For each point, record:

- peak VRAM/RAM
- tier byte-seconds if available
- PCIe/file traffic
- latency or tokens/s converted to a minimization cost
- error/quality metric where relevant.

Then B439 can distinguish:

- static plan activation;
- capacity-dependent cost shift;
- candidate-set change;
- missing observation.

This is safer than attributing every frontier change to memory pressure.

## 10. Measurement discipline

To use the comparator scientifically:

1. preserve plan identity;
2. preserve workload identity;
3. preserve model/input identity;
4. record capacity explicitly;
5. record all objective dimensions used for dominance;
6. mark missing measurements as missing;
7. do not impute a zero cost;
8. use a tolerance only when measurement precision justifies it.

A changed objective coordinate is a fact.

Its causal mechanism remains a hypothesis until separately tested.

## 11. Implementation

Frozen on branch:

- research/static-dynamic-frontier-b439

Files:

- src/finite_ram_lab/static_dynamic_frontier.py
- tests/test_static_dynamic_frontier.py
- analysis/inputs/B439-STATIC-DYNAMIC-FRONTIER-COMPARATOR-v0.1.json
- docs/B439-STATIC-DYNAMIC-FRONTIER-COMPARATOR-v0.1.md

The comparator provides:

- measured frontier construction;
- objective deltas;
- tolerance-aware changed-coordinate detection;
- lost/added frontier IDs;
- measured dominators;
- explanation classification.

Validation:

- identical static replay -> no monotonicity violation
- self cost shift -> correctly classified
- dominator cost shift -> correctly classified
- new/unobserved dominator -> distinguished
- missing larger observation -> distinguished
- tolerance filtering -> PASS
- 5000 deterministic random static replays -> no false violation

Claim ceiling:

SOFTWARE_COMPARATOR_WITH_SYNTHETIC_DYNAMIC_EXAMPLES.

## 12. New result H439 — Frontier Loss is an Instrumentation Target

> Under the B438 static assumptions, disappearance of a frontier plan is not merely an optimizer event. It is a targeted observation that at least one assumption changed.

The comparator turns that event into an investigation queue:

- self cost changed;
- competitor cost changed;
- candidate set changed;
- observation missing;
- or unexplained inconsistency.

This makes a monotonicity violation useful rather than merely surprising.

## 13. Next research direction

The next high-value move is not another abstraction.

It is to produce the first real dynamic observation pair that B439 can ingest.

Two safe candidates remain separate:

### CPU/memcg path

Resume the already-designed B425 one-canary 60-second ambient catcher only after its host-action/software qualification is complete.

### GPU/application path

Use an existing local model/runtime with a bounded capacity knob, preserving the same workload and plan identity, and record two or more capacity points.

Whichever is chosen first, freeze the raw receipts before interpreting frontier changes.
