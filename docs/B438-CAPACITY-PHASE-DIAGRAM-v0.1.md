# B438 — Capacity Phase Diagram and Monotonicity Theorem v0.1

Status: **formal static-cost result on the B436 mixed scenario**. No physical benchmark ran.

## 1. From thresholds to a phase diagram

B437 represented each safe plan by a capacity requirement vector.

B438 adds the exact Pareto set at each capacity cell.

Each RAM/VRAM cell is labelled by the option families visible on the exact frontier.

For the B436 grid:

- 165 capacity cells
- 19 non-empty strategy regimes
- 102 neighboring cells with a changed exact-frontier signature
- 0 neighboring transitions where a previously visible option disappeared

The last observation is not an accident under the current assumptions.

## 2. Capacity Monotonicity Theorem

Let C and C' be capacity vectors with:

C <= C'

componentwise.

Assume:

1. each plan has a capacity-independent resource requirement vector r(p);
2. each constrained resource usage is also included as a minimized Pareto objective;
3. other objective coordinates are capacity-independent for the compared static plans.

Then:

Pareto(C) is a subset of Pareto(C').

In words:

> Increasing capacity can add static Pareto plans, but cannot remove a plan that was already Pareto-optimal.

## 3. Proof

Take a plan p that is Pareto-optimal under C.

Because p is feasible:

r(p) <= C.

Assume for contradiction that p is no longer Pareto-optimal under larger capacity C'.

Then some plan q feasible under C' dominates p.

Because every constrained resource coordinate is itself minimized in the Pareto vector:

r(q) <= r(p).

Therefore:

r(q) <= r(p) <= C.

So q was already feasible under C.

But q also has no worse values on every other objective and is strictly better on at least one.

Therefore q would already have dominated p under C.

Contradiction.

Hence p remains Pareto-optimal after capacity expansion.

## 4. Why this matters

The static capacity phase diagram is not an arbitrary collection of configurations.

It is a monotone growth process.

At tight capacity only a small set of strategies is visible.

As RAM/VRAM expands:

- existing frontier arms remain;
- newly feasible tradeoff arms join.

This produces a directed acyclic strategy graph under monotone capacity expansion.

## 5. B436 strategy sequence

One common VRAM expansion sequence after streamed KV is available is:

tight
-> future-sufficient summary + blocked frontier + borrowed prompt capacity
-> materialized semantic state joins
-> full-VRAM KV joins
-> wide temporalization joins
-> dedicated prompt scratch joins
-> richer expert-residency arms join.

These are additions, not replacements.

A controller therefore does not need to forget the tight-memory solution when the machine has more capacity.

It gains more choices.

## 6. Example: semantic reduction becomes optional, not invalid

Near the low-VRAM boundary the normalized future-sufficient summary may be the only feasible semantic-state choice.

With additional VRAM, the materialized option becomes feasible.

The summary plan remains Pareto-relevant because it still uses less VRAM.

The materialized plan joins because it avoids the modeled reduction compute cost.

Thus the transition is:

mandatory reduction
-> reduction versus materialization tradeoff.

It is not:

reduction strategy replaced by materialization strategy.

## 7. Example: temporalization becomes optional

At tight VRAM:

blocked frontier

is required.

With more VRAM:

wide frontier

joins.

The blocked plan remains Pareto-relevant because it minimizes resident state.

The wide plan joins because it avoids normalized blocking traffic/compute/latency.

Again, capacity reveals an additional tradeoff arm.

## 8. Example: prompt cache borrowing

At tight capacity:

borrow expert-cache slots

is required to avoid a new prompt allocation peak.

At higher VRAM:

dedicated prompt scratch

joins the frontier.

Borrowing remains attractive on the memory axes.

Dedicated scratch becomes attractive on refill/latency axes.

This is exactly the behavior a multi-objective model should preserve.

## 9. 19 regimes in the B436 grid

The 19 non-empty strategy regimes differ by which options have joined the exact frontier.

The grid shows several recurring transitions.

### RAM increases

Common additions include:

- streamed KV;
- larger-RAM expert placement arms;
- richer expert tier combinations.

### VRAM increases

Common additions include:

- materialized semantic state;
- full-VRAM KV;
- wide temporalization;
- dedicated prompt scratch;
- larger GPU expert caches.

The result is a two-dimensional strategy phase diagram rather than one linear tuning curve.

## 10. The theorem depends on keeping memory in the objective

A subtle but important condition is that the constrained resource coordinates are themselves Pareto objectives.

Suppose VRAM is only a hard feasibility constraint and is omitted from the objective vector.

A newly feasible high-VRAM plan might have:

- lower latency;
- lower traffic;
- lower compute;
- equal error

and therefore dominate an old low-VRAM plan once the capacity expands.

Then the frontier can lose old plans.

Including peak memory as an objective prevents this because the high-VRAM plan cannot dominate a lower-VRAM plan on the VRAM coordinate.

This supports the current Live-State Frontier decision to keep tier peaks in the full objective vector.

## 11. Static topology versus runtime behavior

The monotonicity theorem is a **static-cost theorem**.

It can fail as a model of measured runtime when objective coordinates depend on capacity.

For example:

- a plan's latency may fall when extra RAM prevents reclaim;
- transfer cost may change when page residency changes;
- GPU migration behavior may change with free VRAM;
- cache hit rates may change with capacity.

In that case the same nominal plan has different measured objective vectors under C and C'.

Then the theorem's capacity-independence assumption no longer holds.

This gives a clean separation.

### Static activation plane

- plan definitions
- resident requirements
- safe transformations
- static cost estimates
- monotone Pareto-arm growth.

### Runtime pressure plane

- reclaim
- page faults
- migration
- cache hits
- stalls
- measured latency.

The earlier finite-ram memcg work belongs primarily to the second plane.

## 12. Relationship to B437 Activation/Pressure Duality

B437 proposed:

capacity value
=
activation value
+
pressure-relief value.

B438 sharpens the activation side.

Under static costs:

- activation topology is monotone;
- strategy transitions only add Pareto arms.

Therefore any observed disappearance or reversal in a physical experiment is evidence that:

- runtime costs changed with capacity;
- the plan definition changed;
- or the measurement/classification pipeline changed.

That makes monotonicity a useful diagnostic invariant.

## 13. Implementation

Frozen on branch:

- research/capacity-phase-diagram-b438

Files:

- src/finite_ram_lab/capacity_phase_diagram.py
- tests/test_capacity_phase_diagram.py
- analysis/inputs/B438-CAPACITY-PHASE-DIAGRAM-v0.1.json
- docs/B438-CAPACITY-PHASE-DIAGRAM-v0.1.md

The implementation provides:

- exact-frontier strategy signatures;
- signature additions/removals;
- capacity-grid cells;
- neighboring transition edges;
- explicit capacity-expansion monotonicity checks.

Validation:

- B436 non-empty strategy regimes = 19
- changed neighboring signatures = 102
- transitions with removed options = 0
- deterministic 5000 randomized static capacity-expansion instances preserve exact frontier inclusion

Claim ceiling:

FORMAL_STATIC-COST_FRONTIER_THEOREM_ON_B436_GRID.

## 14. New hypothesis H438 — Monotonicity Violation as Runtime Signal

> If a physical system appears to lose a previously Pareto-relevant strategy when only capacity is increased, then at least one non-memory objective is capacity-dependent, or the effective plan semantics changed.

This is experimentally useful.

A future physical sweep can compare:

- static predicted monotone frontier;
- measured runtime frontier.

The difference identifies where pressure, caching, migration, or other dynamic effects enter.

## 15. Next bounce B439

Build a **static-versus-dynamic frontier comparator**.

Input:

- static plan objective vector;
- measured objective vector at several capacities.

Output:

- expected static additions;
- measured additions/removals;
- monotonicity violations;
- which objective coordinate changed enough to explain the violation.

This can later consume:

- B425 ambient pressure receipts;
- GPU memory sweeps;
- Strata runtime tier metrics.

It would finally connect the abstract optimizer back to physical finite-memory observations without mixing the evidence prematurely.
