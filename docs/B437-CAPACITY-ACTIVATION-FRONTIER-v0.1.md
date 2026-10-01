# B437 — Capacity Activation Frontier v0.1

Status: **formal capacity geometry on the B436 mixed scenario**. No physical benchmark ran.

## 1. Core idea

Every safe plan has a per-tier resident requirement vector.

For RAM and VRAM:

r(p) = (R_p, V_p).

A machine with capacity vector:

C = (R, V)

can execute plan p only when:

R >= R_p

and

V >= V_p.

Equivalently:

C >= r(p)

componentwise.

Therefore one plan is feasible over the upper-right orthant rooted at its requirement point.

The scenario's feasible region is the union of those orthants.

## 2. Why one "minimum memory" number is wrong

With multiple independent tiers, there may be no single plan that minimizes every capacity coordinate.

For B436 the minimal safe requirement set is exactly:

- (RAM=8192 MiB, VRAM=10544 MiB)
- (RAM=9776 MiB, VRAM=9356 MiB)

Neither point dominates the other.

The first uses less RAM but more VRAM.

The second spends 1584 MiB of additional RAM to activate streamed KV and saves 1188 MiB of VRAM.

Thus the correct minimum-capacity object is an **antichain**, not a scalar.

## 3. Definition

Let P be the set of safe plans.

Define the requirement set:

R = { r(p) : p in P }.

A requirement vector a dominates b when:

a_j <= b_j for every tier j

and strictly less for at least one tier.

The **Capacity Activation Frontier** is:

A = minimal(R)

under this componentwise order.

A machine is structurally feasible if and only if it covers at least one activation point:

exists a in A such that C >= a.

## 4. B436 activation frontier

The compiler returns:

A = {
  (8192, 10544),
  (9776, 9356)
}

in (RAM MiB, VRAM MiB) order.

So the feasibility boundary is a two-step staircase.

### Region 1

If:

RAM >= 8192

and

VRAM >= 10544

the full-VRAM INT8 KV plan can run with the minimum expert resident budget.

### Region 2

If:

RAM >= 9776

and

VRAM >= 9356

the streamed INT8 KV plan can run.

Capacities below both upper orthants are infeasible in this scenario.

## 5. Why the cliff is exactly 1188 MiB

The B432 INT8 KV pool is:

- full encoded pool = 1584 MiB
- resident streamed GPU subset = 396 MiB

so:

1584 - 396 = 1188 MiB.

At the RAM activation threshold, the minimum required VRAM falls from:

10544

to:

9356

which is also:

1188 MiB.

This is not an arbitrary optimizer artifact.

It is the direct geometry of the source-backed KV placement transformation.

## 6. Option-specific activation frontiers

The same construction can be applied to plans containing a selected option.

### Full INT8 KV

Activation frontier:

- (8192, 10544)

### Streamed INT8 KV

Activation frontier:

- (9776, 9356)

This is the cleanest demonstration of a tier substitution.

### Materialized semantic state

Activation frontier:

- (8192, 11312)
- (9776, 10124)

### Proven future-sufficient summary

Activation frontier:

- (8192, 10544)
- (9776, 9356)

The semantic reduction shifts the VRAM requirement down by 768 MiB under either RAM regime.

### Wide temporalization frontier

Activation frontier:

- (8192, 12080)
- (9776, 10892)

### Blocked temporalization frontier

Activation frontier:

- (8192, 10544)
- (9776, 9356)

Again this isolates the memory-for-work exchange as a capacity shift.

### Dedicated prompt scratch

Activation frontier:

- (8192, 15275)
- (9776, 14087)

### Borrowed expert-cache capacity

Activation frontier:

- (8192, 10544)
- (9776, 9356)

The large gap demonstrates the structural value of phase borrowing: it avoids adding the prompt scratch to peak VRAM.

## 7. Expert-placement activation geometry

The source-anchored expert proxy has several placement arms.

### 20-GiB GPU / 14-GiB RAM

Activation frontier:

- (14336, 22832)
- (15920, 21644)

The second point spends host RAM on KV streaming and lowers required VRAM.

### 12-GiB GPU / 22-GiB RAM

Activation frontier:

- (22528, 14640)
- (24112, 13452)

### 8-GiB GPU / 26-GiB RAM

Activation frontier:

- (26624, 10544)
- (28208, 9356)

### 8-GiB GPU / 8-GiB RAM + file backing

Activation frontier:

- (8192, 10544)
- (9776, 9356)

This shows why low-RAM mapped/file-backed paths expand the feasible region even when they are not necessarily preferred for latency.

## 8. Two different meanings of "cliff"

B437 makes an important distinction.

### A. Combinatorial activation cliff

A capacity boundary is crossed and a plan changes from impossible to possible.

Example:

RAM 9775 -> 9776 MiB

activates streamed KV in B436.

This is discrete even if hardware latency is perfectly smooth.

### B. Runtime pressure cliff

A plan is already legal, but running close to a capacity limit causes:

- reclaim;
- paging;
- swap;
- page migration;
- cache eviction;
- reload;
- latency growth.

This is the type of cliff the older finite-ram pressure-knee experiments observe.

The two phenomena can occur together, but they are not the same.

## 9. A useful decomposition of capacity value

Capacity therefore has at least two distinct marginal values.

### Feasibility value

Does another unit of RAM/VRAM activate a previously illegal plan?

This value is discontinuous at activation boundaries.

### Runtime value

Within an already feasible plan, does more headroom reduce pressure cost?

This may rise sharply near a runtime knee.

This suggests a future controller should not use one generic "memory shadow price."

It should distinguish:

- **activation price**
- **pressure price**

## 10. Geometry generalizes to more tiers

For n resident tiers:

r(p) = (M_1, M_2, ..., M_n).

The activation region of a plan remains an upper orthant.

The global activation frontier remains the componentwise minimal antichain.

Possible future tiers include:

- HBM/VRAM
- pinned RAM
- pageable RAM
- page cache
- CXL memory
- local NVMe cache

Backing storage itself should still be separated from resident capacity.

## 11. Computational implication

A controller can precompute the activation antichain before considering traffic, latency, or error preferences.

This gives a cheap first-stage query:

> Is there any safe plan at all under these capacities?

If not, no amount of scalar cost tuning can help.

If yes, the exact/beam Pareto controller can operate only on the activated candidate region.

This suggests the pipeline:

semantic safety
-> capacity activation frontier
-> runtime/Pareto optimization.

That is cleaner than mixing infeasibility penalties into one objective score.

## 12. Implementation

Frozen on branch:

- research/capacity-activation-frontier-b437

Files:

- src/finite_ram_lab/capacity_activation_frontier.py
- tests/test_capacity_activation_frontier.py
- analysis/inputs/B437-CAPACITY-ACTIVATION-FRONTIER-v0.1.json
- docs/B437-CAPACITY-ACTIVATION-FRONTIER-v0.1.md

The implementation can compute:

- safe-plan requirement vectors;
- componentwise dominance;
- scenario activation antichain;
- option-specific activation antichains;
- capacity membership.

Validation includes:

- the two exact B436 activation points;
- exact full/streamed KV frontiers;
- materialize/reduction frontiers;
- prompt borrowing frontiers;
- expert placement frontiers;
- 10,000 deterministic randomized capacity membership checks against the closed-form two-step staircase.

Claim ceiling:

FORMAL_CAPACITY_GEOMETRY_ON_B436_SCENARIO.

## 13. New hypothesis H437 — Activation/Pressure Duality

> The value of memory capacity is the sum of two qualitatively different effects: discrete activation of new legal plans and continuous or sharply nonlinear runtime-pressure relief inside already legal plans.

This offers a direct bridge back to the earlier memcg pressure-knee work.

The B425 ambient catcher can eventually measure pressure behavior, while the B437 activation frontier predicts structural plan boundaries.

They should remain separate evidence streams until a later synthesis.

## 14. Next bounce B438

The next mathematical step is a **capacity phase diagram**.

For each capacity cell:

1. identify which activation orthants cover it;
2. enumerate exact Pareto plans;
3. label which transformation families are visible;
4. detect cells where crossing one capacity boundary changes the transformation set.

Then compute a transition graph such as:

tight
-> +RAM
-> KV MOVE activated
-> +VRAM
-> semantic materialization arm appears
-> +VRAM
-> wide temporalization appears
-> +RAM/VRAM
-> richer expert-residency arms appear.

That would give Finite RAM Lab a map of strategy regimes rather than isolated thresholds.
