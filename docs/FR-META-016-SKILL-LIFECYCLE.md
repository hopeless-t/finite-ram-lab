# FR-META-016 — Skill Lifecycle and Residency Governor

Status: **DOGFOOD GOVERNANCE CANDIDATE**

Parent: **FR-META-015**

## New failure mode

Compiling decisions into skills reduces repeated reasoning, but an unbounded
skill catalog can become a new context-pressure source.

Finite RAM therefore needs to govern skills the same way it governs other
resident state.

## Skill states

CANDIDATE
: a rule exists but lacks qualifying replay evidence.

QUALIFIED
: one bounded positive replay with explicit scope and intact invariants.

STABLE
: at least two positive replays across at least two examples with no
  contradiction.

QUALIFIED_NEGATIVE
: direct scoped failure evidence says a candidate action should not be promoted
  under the observed conditions.

RETIRED
: invalidation or contradictory evidence has appeared.

BLOCKED
: scope is unknown, invariants fail, or the proposed skill expands authority.

INSUFFICIENT_EVIDENCE
: required lifecycle evidence is missing.

## Resident context

Only these states are eligible for the normal resident skill set:

- QUALIFIED;
- STABLE;
- QUALIFIED_NEGATIVE.

Retired, blocked, candidate, and insufficient skills move to cold history.

Cold does not mean deleted.

Receipts and failure specimens remain durable so a future theory update can
rehydrate them.

## Mutation boundary

The lifecycle governor may update one field automatically:

    maturity

It may not silently mutate:

- trigger predicates;
- actions;
- Monte Carlo policy;
- provenance;
- invalidation conditions;
- execution authority.

Changing those semantics is a new research transition, not a maturity update.

## Current examples

EXACT_REUSE_BEFORE_SAMPLE_REDUCTION now has repeated evidence across several
independent exact-reuse experiments including the skill-routed FR-META-015
dogfood and therefore remains STABLE.

CANCEL_SUPERSEDED_NON_MAIN_CI has two independent observed cancellations and
remains STABLE.

The FR-META-013 cache failure becomes a QUALIFIED_NEGATIVE scoped guard.

An old rule contradicted by new evidence becomes RETIRED and leaves resident
context while remaining in cold provenance.

## Why this is Finite RAM

Skill compilation alone is analogous to compression.

Residency governance adds eviction.

The desired reasoning-memory hierarchy becomes:

    full evidence history      = cold backing store
    compiled skill catalog     = indexed intermediate tier
    matching stable capsules   = resident working set
    current primary action     = active state

That prevents the optimization layer from recreating the context problem it was
built to solve.

## Claim ceiling

**SKILL_LIFECYCLE_AND_RESIDENCY_GOVERNANCE_ONLY**
