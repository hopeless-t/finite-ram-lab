# B434 — Exact Bounded Frontier Controller v0.1

Status: **tiny-window exact optimization model**. No physical benchmark ran.

## 1. Purpose

B433 froze the Live-State Frontier taxonomy v0.2.

B434 turns that taxonomy into a controller that can answer a bounded question:

> Given several legal representations/schedules for each state, which combinations are safe, fit the independent memory tiers, and are not dominated in the full cost vector?

The controller is deliberately exact and small. It is an oracle for later heuristics, not a production scheduler.

## 2. Input

Each semantic state exposes one or more StateOption records.

An option specifies:

- resident bytes by tier;
- byte-seconds by tier;
- transfer traffic;
- compute/recompute cost;
- latency cost;
- error cost;
- whether semantic state is released;
- whether release has a proof;
- whether owners are merged;
- whether sharing has a proof;
- whether a non-zero error has an explicit bound.

## 3. Safety is evaluated before optimization

The controller rejects an option if any of these hold:

### Unproven release

releases_semantic_state = true

and

release_proven = false.

### Unproven owner merge

merges_owners = true

and

sharing_proven = false.

### Unbounded lossy change

error_cost > 0

and

error_bound_known = false.

Therefore a low-memory option cannot enter the Pareto search merely because it looks numerically attractive.

This preserves the fail-closed behavior from B426/B433.

## 4. Capacity feasibility

After semantic safety, the controller aggregates resident bytes independently for every tier.

A plan is feasible only if:

for every resident tier j,

M_j <= C_j.

Unknown capacities fail closed: a plan that consumes a tier absent from the capacity map is rejected.

This directly fixes the flat-physical-byte problem exposed by Strata.

## 5. Objective vector

For the set of capacity tiers, the objective vector is:

1. peak resident bytes on each tier;
2. byte-seconds on each tier;
3. traffic bytes;
4. compute cost;
5. latency cost;
6. error cost.

The exact controller does not assign scalar weights.

It removes only plans that are Pareto dominated.

## 6. Dominance

Plan A dominates B when:

- A is no worse than B on every objective component;
- A is strictly better on at least one component.

This preserves genuine exchange choices.

For example:

- a resident plan may use more VRAM but no transfer;
- an offload plan may use less VRAM but more RAM/traffic/latency;
- a compressed plan may use less VRAM while spending a bounded error budget.

None should be silently chosen by the controller without an external preference.

## 7. Normalized example

Frozen in:

- analysis/inputs/B434-BOUNDED-CONTROLLER-NORMALIZED-v0.1.json

Capacities:

- VRAM = 6 units
- RAM = 16 units

One semantic state has three legal alternatives.

### Resident

- VRAM = 8
- no traffic
- no latency cost
- no error

This would be attractive with enough VRAM, but it is infeasible under the 6-unit bound.

### Offload

- VRAM = 2
- RAM = 8
- traffic = 20
- latency = 3
- error = 0

Feasible.

### Bounded-loss compression

- VRAM = 4
- RAM = 0
- traffic = 0
- latency = 0
- bounded error = 0.1

Feasible.

The exact frontier retains both offload and compression.

Why:

- offload has zero error but pays RAM/traffic/latency;
- compression has no offload cost but pays an explicit error budget.

The controller refuses to decide which trade is preferable without a higher-level policy.

## 8. Relationship to real systems

The option abstraction can represent the previously studied systems.

### FlashAttention

For score state:

- materialize;
- or proven future-sufficient reduction.

The reduction option has release_proven=true.

### Checkmate / DTR

- retain activation;
- or release with recomputation.

The rematerialization option has release_proven=true and compute_cost>0.

### Strata KV

- full VRAM residency;
- host-backed streamed residency;
- alternative quantized representations with a measured/known error dimension.

### Strata experts

- VRAM hot set;
- RAM complement;
- mapped/file fallback;
- shared immutable host copy.

### GEMMul8

- larger m/n/k block;
- smaller block with more invocation/traffic cost;
- a future p-axis option only after a reconstruction proof exists.

## 9. Why exact tiny windows matter

The full problem is combinatorial.

If state i has k_i options, exact enumeration examines:

product_i k_i

combinations before filtering.

That is appropriate only for small windows.

But those exact windows provide a valuable oracle:

- verify a heuristic never returns unsafe plans;
- measure heuristic regret against the true local Pareto frontier;
- study which objective dimensions heuristics systematically sacrifice;
- construct adversarial cases.

This mirrors the lab's existing preference for bounded local reasoning rather than one huge opaque optimizer.

## 10. Validation

Frozen files:

- src/finite_ram_lab/bounded_frontier_controller.py
- tests/test_bounded_frontier_controller.py
- analysis/inputs/B434-BOUNDED-CONTROLLER-NORMALIZED-v0.1.json
- docs/B434-EXACT-BOUNDED-FRONTIER-CONTROLLER-v0.1.md

Authoring validation:

- unproven release rejection: PASS;
- unproven owner sharing rejection: PASS;
- lossy option with unknown error bound rejection: PASS;
- independent tier capacity filtering: PASS;
- dominated plan removal: PASS;
- non-dominated memory-exchange alternatives retained: PASS;
- proven summary-release option allowed: PASS;
- deterministic 10,000 randomized frontier cases: no dominated plan survived.

Claim ceiling:

EXACT_TINY_WINDOW_MODEL_ONLY.

## 11. Current research picture

The research stack is now:

Semantic obligation
↓
safe release / ownership proof
↓
representation
↓
axis temporalization
↓
tier placement
↓
phase borrowing
↓
lifetime
↓
exact bounded Pareto selection

The important property is that optimization never precedes correctness proof.

## 12. B435 candidate — heuristic versus oracle

The next bounce should introduce a cheap heuristic suitable for larger windows.

Candidate heuristic:

1. discard unsafe options;
2. calculate per-tier pressure shadow prices from capacity ratios;
3. score each option by avoided pressured-tier byte-seconds;
4. subtract traffic/compute/latency/error penalties;
5. greedily choose locally beneficial changes;
6. repair capacity violations;
7. compare against B434 exact frontier on thousands of small random instances.

Primary measurements:

- feasibility rate;
- dominated-output rate;
- distance/regret to exact Pareto set;
- runtime/combinatorial reduction;
- failure patterns near tier capacity cliffs.

The heuristic should not be considered successful merely because it saves memory.
