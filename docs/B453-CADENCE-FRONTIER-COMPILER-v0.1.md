# B453 — Symbolic Cadence Frontier Compiler v0.2

Status: **corrected symbolic objective-quotient model**. No physical experiment ran.

## 1. The first generalization failed — usefully

The first B453 draft claimed:

> one smallest cadence per intervention-count class reproduces the full Pareto plan-ID frontier.

Random qualification immediately found a counterexample.

For:

- F=26
- K={1,3,6,8,18,21,23}
- B=117.7150528
- H=86.0395173

the exact plan-ID frontier is:

**{18,21,23}.**

All three cadences:

- are capacity-clamped to the same peak;
- have the same pressure state;
- have the same 2-call intervention count.

Therefore they have exactly the same objective vector.

None strictly dominates another as a plan identity.

The original plan-ID claim was too strong.

## 2. Corrected object: the objective-vector quotient

For optimization, exact tied plan identities need not create separate decision points.

Define two plans as equivalent when their complete modeled objective vectors are identical.

Then the quotient frontier contains one canonical representative per distinct Pareto objective vector.

For the counterexample:

plan-ID frontier:
- 18
- 21
- 23

objective-vector quotient:
- representative 18

with tie group:

{18,21,23}.

This is the corrected B453 claim.

## 3. Intervention classes

Input:

- fixed span F;
- arbitrary positive discrete cadence set K;
- transient-base estimate B.

Intervention cost:

**N(K)=ceil(F/K).**

Cadences with equal N(K) form an intervention class.

The compiler selects the smallest K as the canonical optimizer representative.

Larger same-class cadences remain available as:

- mechanism probes;
- exact tied plan identities under clamp;
- physical continuity checks.

They are not erased from evidence.

## 4. Symbolic activation rule

Each canonical class representative k_i has a pressure-free threshold:

**T_i=B+k_i.**

At capacity H the canonical objective frontier contains:

1. every representative whose threshold has been crossed;
2. the minimum-intervention fallback representative.

This compiles the set of **distinct Pareto objective vectors**.

It does not promise to enumerate every plan ID that ties exactly on one of those vectors.

## 5. B447 remains unchanged

For:

- F=96
- K={32,48,64,80,96}
- B=78.609

classes are:

- 3 calls -> 32
- 2 calls -> 48 with 64/80 as same-class mechanism cadences
- 1 call -> 96.

Canonical representatives:

**{32,48,96}.**

Search-space reduction:

**40%.**

For the actual B447 capacity points 144/160/176, 64/80 are not merely exact ties in the expected twin; they are dominated by 48 on the modeled PRIMARY vector.

## 6. Plan frontier versus decision frontier

B453 now freezes a distinction.

### Plan-ID Pareto frontier

Preserves every nondominated physical plan identity, including exact objective ties.

Useful for:

- auditability;
- physical mechanism comparison;
- provenance.

### Objective-quotient frontier

Preserves every distinct Pareto objective vector with one canonical representative.

Useful for:

- optimizer search;
- controller state compression;
- exact/beam complexity reduction.

A compiler may compress the second without destroying the first evidence lane.

## 7. Corrected validation

The first random generalization test failed almost immediately and produced the counterexample above.

After correcting the theorem, the compiler was compared against a brute-force **canonical objective frontier** over:

- 20,000 deterministic random discrete cadence systems;
- random span sizes;
- random candidate subsets;
- random transient-base values;
- random clean-floor proxies;
- random capacities.

Result:

**symbolic objective quotient = brute-force canonical objective frontier in every case.**

## 8. Revised H453 — Control-Choice Quotienting

> Control settings that are distinct physical plans but map to the same Pareto objective vector may be quotient-compressed for optimization, provided their identities remain available in a separate evidence/mechanism lane.

This is a safer and more general statement than the original draft.

It also mirrors Live-State Frontier more precisely:

- preserve semantic/evidentiary identity;
- compress only the representation needed for the current decision.

## 9. Next direction

B454 should integrate the quotient compiler with B434/B435 and explicitly carry both:

- canonical optimizer representative;
- provenance tie group.

Then measure reduction in exact combinations and beam width without losing the ability to map a selected objective point back to every physically equivalent mechanism candidate.
