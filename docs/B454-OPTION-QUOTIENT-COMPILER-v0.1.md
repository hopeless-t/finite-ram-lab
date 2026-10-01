# B454 — Option Quotient Compiler v0.1

Status: **exact additive objective-quotient model**. No physical experiment ran.

## 1. From cadence-specific compression to a general compiler pass

B453 established a corrected distinction:

- several physical plan IDs may tie exactly on the Pareto frontier;
- an optimizer needs only one representative of each distinct objective vector;
- physical provenance must still be retained.

B454 asks whether that compression can happen **locally inside option groups** before the general Cartesian-product controller runs.

Under additive objectives, it can.

## 2. Local Quotient Preservation theorem

Suppose a global plan selects exactly one option from each group.

The global objective vector is the componentwise sum of the selected local objective vectors.

All coordinates are minimized.

Within each option group:

1. remove locally dominated choices;
2. group exact objective-vector ties;
3. keep one canonical representative per vector;
4. attach every tied physical ID as provenance.

Then the set of **distinct global Pareto objective vectors** is unchanged.

## 3. Why local dominance pruning is safe

Let local choice a dominate local choice b.

For any identical selection of the remaining groups, represented by future vector F:

a + F <= b + F

componentwise, with at least one strict improvement.

Therefore b cannot participate in a distinct global Pareto vector that a cannot dominate.

This is the same additive-prefix logic used by B435, moved earlier into compilation.

## 4. Why exact-vector quotienting is safe

If two local choices have the exact same objective vector:

a = b

then for every future vector F:

a + F = b + F.

They create identical global objective vectors.

Keeping both increases plan-ID multiplicity but cannot create another point in objective space.

One canonical representative is sufficient for optimization.

## 5. Provenance is not discarded

B454 does not delete physical identity.

A canonical quotient option stores:

- its canonical choice ID;
- the full provenance set of tied physical choices.

For the B453 counterexample:

- physical tied plans = {18,21,23}
- canonical optimizer representative = 18
- provenance = {18,21,23}.

If the optimizer later selects that objective point, the evidence layer can still inspect all physically equivalent candidates.

## 6. Fixed reduction example

Two option groups:

- raw sizes = 5 and 4
- quotient sizes = 2 and 3.

Cartesian combinations:

- before = 20
- after = 6.

Reduction:

**70%.**

The distinct global Pareto objective vectors remain unchanged.

## 7. Relationship to B434/B435

The controller stack now has three distinct reduction opportunities.

### Compile-time local reduction — B454

- remove local dominance;
- quotient exact local objective ties.

### Exact bounded controller — B434

- enumerate the remaining combinations;
- enforce capacity and safety;
- return exact Pareto frontier.

### Beam controller — B435

- when exact combinations are still too large;
- prune partial Pareto sets under a beam bound.

The preferred order becomes:

raw choices
-> semantic/safety gate
-> local quotient compiler
-> exact bounded controller when small
-> Pareto beam when still large.

## 8. Relationship to mechanism arms

A locally dominated option can be removed from **optimizer search** while remaining in the **experimental evidence lane**.

This matters for B447:

- 64/80 MiB cadence arms may be dominated under the frozen PRIMARY vector;
- they remain valuable for clamp-threshold localization.

So the experiment matrix and the optimizer candidate matrix need not be identical.

## 9. Random exact validation

B454 generated 5,000 deterministic random additive systems with:

- 1..4 option groups;
- 1..5 choices per group;
- 2..5 objective dimensions;
- integer objective coordinates to deliberately create ties.

For each system:

1. enumerate the full Cartesian product;
2. compute distinct exact global Pareto objective vectors;
3. locally quotient every group;
4. enumerate the reduced product;
5. recompute the global Pareto objective vectors.

Result:

**identical frontier vector sets in every case.**

## 10. New principle H454 — Separate Plan Multiplicity from Decision Multiplicity

> The number of physically distinct plans can be much larger than the number of distinct decision-relevant objective states. Optimization should scale with the latter while evidence retains the former.

This is another instance of the Live-State Frontier pattern:

retain the information obligation,
discard redundant representation.

## 11. Next direction

B455 should connect the quotient compiler to the existing B434 StateOption representation and measure real combination reduction on the mixed B436 scenario plus the B447 cadence group.

The important checks are:

- safety flags survive quotienting;
- exact tied options are quotiented only when safety/provenance semantics are compatible;
- capacity usage remains in the objective/feasibility representation;
- exact B434 frontier is unchanged after quotient compilation.
