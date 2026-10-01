# B459 — Exact DP Group-Order Optimization v0.1

Status: **exact small-n ordering result**. No physical experiment ran.

## 1. Why order matters

B458 showed that exact prefix Pareto DP replaces full Cartesian enumeration when intermediate frontiers remain narrow.

But the intermediate frontier depends on group order.

The final additive objective sum is commutative.

The computational path is not.

Therefore two permutations of the same groups can produce:

- the same final exact frontier;
- very different cumulative expansion counts.

## 2. Exact subset-order oracle

For n groups, B459 constructs the exact Pareto frontier for every subset of groups.

For each transition:

subset S
-> add group g

it records the number of safe feasible prefix states expanded.

That transition count becomes an edge cost.

A second dynamic program over subsets finds the minimum-cost path from:

empty subset
to
all groups.

For seven groups:

- subsets = 2^7 = 128
- possible directed add-one-group transitions = 448.

This avoids enumerating all 7! orderings.

## 3. Order invariance

Under the current model:

- each group is selected exactly once;
- objectives add componentwise;
- safety is local/frozen;
- capacities depend only on the summed resident vector.

Thus any complete permutation represents the same set of full plans and the same final distinct Pareto objective vectors.

B459 validates this on:

- the B436+B447 mixed scenario;
- 100 deterministic random four-group systems.

No final-frontier mismatch was observed.

## 4. Fixed mixed scenario

The seven groups are:

- strata_kv
- strata_experts
- strata_prefill
- semantic_reduction
- temporalization
- idle_lifetime
- release_cadence.

### Original order

Total expanded states:

**578**

Final frontier:

240 points.

### Greedy order

The immediate-cost greedy heuristic chooses:

idle_lifetime
-> semantic_reduction
-> strata_kv
-> strata_prefill
-> temporalization
-> strata_experts
-> release_cadence.

Expanded states:

**534**

Savings:

**7.61%**

This helps only modestly.

### Exact optimal order

The subset-DP oracle chooses:

strata_kv
-> strata_prefill
-> temporalization
-> release_cadence
-> idle_lifetime
-> semantic_reduction
-> strata_experts.

Expanded states:

**367**

Savings versus original:

**36.51%**

The exact final frontier remains the same 240 points.

## 5. Why the optimal order wins

The clearest example is the five-option release-cadence group.

Original order:

- input prefix frontier = 80 states
- release-cadence expansion = 80 * 5 = 400 states.

Optimal order:

- cadence arrives when the prefix frontier has only 5 states
- expansion = 5 * 5 = 25 states.

So a high-cardinality group is not intrinsically expensive.

Its cost is:

current frontier width
x
group expansion width.

Putting it earlier can be much cheaper if the early frontier is narrow.

## 6. Why immediate greedy misses this

The greedy heuristic minimizes the next transition's immediate expansion count.

That favors tiny groups early.

But it ignores whether a slightly more expensive group would sharply reduce the frontier before a later high-cardinality group.

B459 therefore finds:

- greedy savings 7.6%
- optimal savings 36.5%.

This is a strong lookahead effect.

## 7. New principle H459 — Frontier-Width Scheduling

> In exact Pareto DP, option groups should be scheduled to control the width of the surviving prefix frontier, not merely by local option count or immediate expansion cost.

This is analogous to join ordering in databases:

the same logical result can have very different intermediate-state sizes depending on composition order.

## 8. Controller architecture consequence

The exact controller stack now becomes:

semantic/safety gate
-> local quotient
-> choose group order
-> exact prefix Pareto DP
-> switch to quotient-aware beam only if frontier width exceeds budget.

The raw Cartesian product is no longer the natural complexity estimate.

A better estimate is the cost of the ordered prefix frontier trajectory.

## 9. Qualification

Isolated research-lane tests:

- 3 tests
- 3 PASS
- runtime 36.087 s
- stderr SHA-256: sha256:c3ee9457abe59d61a5139142a53df40d8f679da8fec1550d0c740078c6b9791e.

Fixed-scenario order output digest:

sha256:50a913227537ea2cc4dd14ca02c3fd7ee421f3a1e0cde21b8fe1c97edbe52288

## 10. Boundary

The exact subset-order oracle scales exponentially with group count.

It is appropriate for:

- small-n exact scheduling;
- offline oracle generation;
- heuristic evaluation.

It is not yet the large-n ordering policy.

## 11. Next direction

B460 should learn a cheap lookahead heuristic from the exact B459 oracle.

Candidate heuristics:

- one-step frontier-size minimization;
- two-step expansion lookahead;
- estimated future cost = current expansion + resulting frontier width * remaining-group scale;
- beam-width-risk score.

The heuristic should be evaluated against the exact order oracle on many random small systems, then used for larger systems where 2^n ordering is too expensive.
