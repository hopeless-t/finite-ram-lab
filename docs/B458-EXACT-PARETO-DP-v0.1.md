# B458 — Exact Pareto Dynamic Program v0.1

Status: **exact within the current B434 model**. No physical experiment ran.

## 1. Observation

B435 already contained a key fact:

> At one fixed prefix depth, every surviving partial plan has the same remaining option groups. Therefore a dominated prefix can never become nondominated by adding the same future choice.

B435 used that fact before a lossy beam truncation.

B458 removes the truncation.

The result is an exact dynamic Pareto program.

## 2. Algorithm

Start with the empty plan.

For each option group:

1. expand every currently surviving prefix by every safe option;
2. reject capacity-infeasible prefixes;
3. compute the exact Pareto set at that prefix depth;
4. quotient exact objective-vector ties only when semantic paths are identical;
5. retain factorized provenance;
6. continue with the reduced prefix set.

There is no beam width.

There is no scalar pressure-score truncation.

## 3. Exactness argument

Let prefix p dominate prefix q at depth d.

Every future completion adds the same selectable future vector F to either prefix.

Therefore:

p + F <= q + F

componentwise, with at least one strict coordinate preserved.

Because resident capacity is also no larger for p, any future completion feasible from q is also feasible from p under the same added future choice.

Thus q cannot produce a distinct globally Pareto-optimal objective vector.

It is safe to discard q permanently.

Induction over prefix depth gives the exact final frontier.

## 4. Tie quotient

Exact same-semantic prefix ties have identical objective vectors.

Adding the same future choice preserves equality.

Therefore one canonical decision state is sufficient for optimization, while B457-style factorized provenance records the represented source options and tied-path count.

Semantic-distinct ties remain separate.

## 5. Random exact validation

B458 compares the dynamic program against the original B434 Cartesian exact controller on:

- 1,000 deterministic random StateOption systems;
- 1..4 state groups;
- safe and unsafe options;
- semantic release flags;
- duplicate plan identities;
- finite RAM/VRAM capacities.

Result:

**0 frontier-vector mismatches.**

Qualification:

- 3 tests
- 3 PASS
- runtime 10.160 s
- stderr SHA-256: sha256:c1d0291bbc4c07e28b9c8f245fd472767d4f4149b917ace803e22adf9735836a

## 6. Redundancy-heavy synthetic panel

The B456 200-case redundancy panel was replayed.

Compared with full Cartesian combination count, the DP expanded:

- mean 45.00%
- minimum 24%
- maximum 56%.

Mean values:

- expanded states = 40.685
- maximum prefix frontier states = 13.29
- final frontier states = 13.29.

Output digest:

sha256:ea3db750d7f668c41d361d3d398c3b156f753e408023b51a04ed682f036e0510

This is where exact dynamic pruning pays strongly.

## 7. Fixed B436 + B447 mixed scenario

Raw Cartesian combinations:

**640**

DP total expanded states:

**578**

Ratio:

**90.31%**

Exact frontier:

**240 states**

Prefix progression:

- depth 1: 2 expansions -> 2 frontier
- depth 2: 8 -> 8
- depth 3: 16 -> 12
- depth 4: 24 -> 24
- depth 5: 48 -> 40
- depth 6: 80 -> 80
- depth 7: 400 -> 240.

This is an important negative result.

The fixed mixed scenario does not have enough early dominance to yield a dramatic reduction in its current group order.

The final five-option cadence group arrives after an 80-state prefix frontier and therefore creates 400 final expansions.

## 8. Timing reference

A small three-repetition local software timing reference gave:

- B434 Cartesian exact mean ~= 1.787 s
- B458 DP mean ~= 1.351 s
- ratio ~= 1.32x.

This is environment-dependent and not the primary claim.

The robust claims are:

- exact frontier equality;
- prefix state counts;
- absence of beam approximation.

Timing output digest:

sha256:7fdf9f619aa8b02bf39942e754a5e4c2559408e105a723de5ff8e478622a33e8

## 9. Architectural consequence

The controller stack changes.

Previously:

small problem -> B434 full Cartesian exact
large problem -> B435 beam

Now a better sequence is:

semantic/safety gate
-> local quotient
-> **B458 exact prefix-DP**
-> only if prefix frontier itself grows beyond budget, switch to B457 quotient-aware beam.

This postpones approximation until exact decision-state growth actually demands it.

## 10. New principle H458 — Exactness Until Frontier Growth

> Approximation should be triggered by growth of the surviving decision frontier, not by the raw Cartesian plan count.

A huge raw product may still be cheap if local/prefix Pareto structure collapses aggressively.

A modest raw product may still have a broad frontier and remain expensive.

## 11. Next direction

The fixed mixed scenario exposes the next optimization target:

**group ordering.**

The exact DP cost depends strongly on which option group is expanded first.

Global additive semantics are commutative, but prefix frontier widths are not.

B459 should search for an ordering that minimizes cumulative expanded states while preserving the exact final frontier.
