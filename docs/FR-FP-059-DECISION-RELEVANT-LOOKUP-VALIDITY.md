# FR-FP-059 — Decision-relevant validity gate for compiled rent lookup

Status: **COMPILED LOOKUP VALIDITY CANDIDATE**

Parent: **FR-FP-058**

## Why

FR-FP-058 compiles the fully physical memory-rent policy family into a small exact hot lookup.

Its first invalidation contract is deliberately conservative:

- physical policy evidence changes;
- semantic service changes;
- physical actuation changes;
- resident byte-time changes.

That contract is safe, but it can over-invalidate.

An evidence field may change without changing any admissible scalar memory-rent decision.

Examples:

- add the same semantic-service offset to every path;
- add the same actuation offset to every path;
- add the same resident MiB-round offset to every path;
- update metadata such as representative rent or evidence labels;
- make a scalar-unsupported path more expensive while it remains off the scalar lower envelope.

Recompiling the hot lookup for those mutations is decision-irrelevant work.

## New validity contract

The hot lookup is itself the resident decision certificate:

    supported path order
    + crossover thresholds

When physical evidence updates:

1. rebuild only the eight-line scalar lower envelope in shadow;
2. compare the candidate path order and thresholds with the hot capsule;
3. keep the hot lookup if the surfaces are numerically equivalent;
4. invalidate and recompile only if the decision surface changes.

Normal memory-rent queries still use only the hot interval lookup.

No DP/knapsack is re-run per query.

## Numerical equivalence

Boundary equality uses a machine-precision-scaled tolerance derived from the FR-FP-058 crossover contract.

This is not policy slack.

It exists only to avoid invalidation caused by floating representation residue.

## Mutation panel

Expected KEEP cases:

- metadata-only changes;
- common semantic-service offset;
- common physical-actuation offset;
- common resident MiB-round offset;
- making scalar-unsupported P1 more expensive.

Expected INVALIDATE cases:

- supported P3 service change;
- supported P5 actuation change;
- supported P6 resident-cost change;
- removal of supported P4.

The test therefore distinguishes:

    evidence changed

from:

    admissible decision changed

## North-Star consequence

The lifecycle becomes:

    rich physical evidence cold
      -> compiled rent lookup hot
      -> evidence update event
      -> tiny shadow surface verifier
      -> keep hot lookup when decision-equivalent
      -> rehydrate/recompile only on decision-surface change

This is decision-relevance pruning applied to the validity lifecycle of a compiled physical policy.

## Claim ceiling

**DECISION_SURFACE_VALIDITY_GATE_FOR_THE_FP058_SCALAR_MEMORY_RENT_LOOKUP_ONLY**
