# FR-META-014 — Decision Skill Compiler

Status: **DOGFOOD COMPILATION CANDIDATE**

Parent: **FR-META-013**

## Hypothesis

Repeated research decisions should stop consuming full-history reasoning once
their applicability boundary has been demonstrated.

The correct unit to compile is not a naked answer.

It is a skill capsule containing trigger facts, action, Monte Carlo policy,
maturity, evidence PRs, invalidation conditions, and global invariants.

This lets later bounces ask a small router before re-reading the full research
history.

## Source surface

The frozen FR-META-004 through FR-META-013 method documents contain 17,417
characters across ten files.

FR-META-014 compiles the repeated decisions from that history into thirteen
machine-readable skills.

The current catalog is required to serialize to less than 30 percent of that
source surface.

A typical selected exact-reuse capsule, including global invariants, must be
less than 5 percent of the source-history character count.

This is a context-surface measurement, not a claim about model-internal token
usage.

## Positive skills

Examples include:

- exact deterministic reuse before reducing scientific samples;
- skip Monte Carlo when the routing topology is exact;
- run Monte Carlo when the decision is uncertain and loss-sensitive;
- publish one coherent transition as an atomic bundle;
- qualify meta panels inside general CI;
- cancel superseded non-main same-head CI;
- materialize a final child only after the parent receipt is frozen.

## Guard skills

Some compiled skills exist to preserve evidence rather than accelerate it:

- never cancel main CI;
- preserve real runtime benchmarks when runtime is itself the measured signal;
- keep pre-receipt build-ahead ephemeral;
- preserve failure specimens before theory update.

## Negative skills

Failures are compilation material too.

FR-META-013 becomes CACHE_REUSE_PROVE_SCOPE_FIRST.

If a cache candidate has no proven producer-to-consumer restore path, the
compiled action is REJECT_CACHE_PROMOTION.

The point is to avoid spending future context reconstructing the same failed
assumption.

## UNKNOWN semantics

A skill is selected only when every trigger fact is explicit.

If some trigger facts match but another required fact is missing, the compiler
returns the missing field in the unresolved set.

It does not guess.

For example, cache_candidate=true with cache_restore_proven unknown does not
select either a negative or positive cache action.

It falls back to evidence gathering or the full research loop.

## Skill maturity

The first catalog distinguishes:

- STABLE / STABLE_GUARD for repeated evidence;
- QUALIFIED / QUALIFIED_GUARD for one bounded qualification;
- QUALIFIED_NEGATIVE for direct failure evidence that blocks promotion.

Maturity is not execution authority.

## Context compiler

Input: an explicit fact dictionary.

Output: global invariants, matching compact skills, unresolved facts, and a
primary action.

If no skill applies, the primary action is NO_COMPILED_DECISION and the caller
returns to the full L0/L1/L2 loop.

## Why this is Finite RAM

This is the same research idea at the reasoning layer.

Full history is the cold backing store.

Compiled skill capsules are the small resident working set.

Only the sufficient decision state is made resident for the current question.

The research loop therefore begins to apply its own North Star to itself:
preserve qualified semantics while minimizing simultaneous resident context.

## Authority boundary

Decision skills may reduce re-reading and re-reasoning.

They do not grant host execution, paid resource use, live memory mutation,
merge authority, threshold mutation, or retry permission after UNKNOWN
delivery.

## Next

Dogfood the compiler prospectively.

For every new meta bounce record whether a compiled skill resolved the decision,
selected capsule characters, full-history fallback count, invalidation events,
and later reversals.

Then measure qualified decision survival divided by resident context
characters, and promote only if correctness and failure capture remain intact.

## Claim ceiling

**COMPILED_DECISION_ROUTING_AND_CONTEXT_SURFACE_ONLY**
