# FR-P9-001 — Minimum Sufficient Resident Projection

Status: candidate experiment on top of FR-FP-058.

## Why Part 9 restarts here

The recent physical placement chain showed that:

- capacity is a hard maximum, not a utilization target;
- immediate semantic optimum can lose after migration cost is priced;
- partial migration can beat both HOLD and immediate semantic optimum;
- additional observation or model refit should be pruned when it cannot change a qualified decision;
- a fully physical memory-rent policy family can be compiled into a small hot lookup while richer typed evidence remains cold.

The next question is therefore no longer merely "what bytes should stay in RAM?" It is:

> What is the minimum runtime projection of canonical meaning that must be resident for one unit of verified work?

This is also the direct bridge to PCG: world truth can stay canonical while frame, generation, verification and recovery phases materialize different bounded projections.

## Core split

```text
Canonical semantic state
        |
        | compile for WorkUnit + contract
        v
Minimum sufficient runtime projection
        |
        +-- decision
        +-- verification
        +-- recovery
        +-- capability
```

The experiment deliberately separates:

```text
Canonical truth != runtime representation
Runtime representation != physical residency
Residency != placement
Placement != authority
Decision equality != verification equality != recovery equality
```

## Fixture

The synthetic canonical universe contains PCG-shaped atoms such as:

- world seed and chunk recipe;
- topology and collision rules;
- generator and verifier capabilities;
- geometry/material projections;
- provenance, checkpoint and recovery recipe;
- deliberately irrelevant cold atoms such as distant world chunks, authoring UI state and analytics history.

Three phase-shaped work units are frozen:

- `GENERATE_CHUNK`
- `RENDER_NEAR_FIELD`
- `VERIFY_COLLISION`

## Arms

### FULL

Every canonical atom is resident. This is the correctness reference, not the desired architecture.

### DECISION_ONLY

Compile only the immediate decision dependency closure. This is an adversary.

It is expected to look correct if the oracle checks only the immediate decision, while silently dropping verification, recovery or capability requirements.

### COMPILED

Take the union of the dependency closures for all four declared contract planes:

- decision;
- verification;
- recovery;
- capability.

## Oracles

The compiled projection passes only if:

1. its complete contract result equals FULL for every work unit;
2. every selected atom has a removal witness: deleting it breaks at least one contract plane;
3. the DECISION_ONLY adversary is rejected as incomplete;
4. compiled resident byte-rounds are lower than FULL;
5. projections differ across work/phase, proving that canonical truth does not imply one universal resident set.

The experiment fails closed on unknown atoms and dependency cycles.

## Why this is PCG

A generated world can be much larger than the set required for the current frame or generation step.

The canonical world may include source recipes, provenance, distant cells, editor metadata and future variants. The runtime should materialize only the slice needed for the current semantic contract.

That gives a common form for:

```text
world chunk streaming
asset LOD / representation selection
procedural regeneration
validator residency
AI context/tool residency
model expert/layer residency
repository/evidence working sets
```

The common problem is not "cache more". It is:

> compile the smallest sufficient projection, then choose where and how to realize it.

## What this experiment does not prove

- no physical RAM saving is claimed yet;
- no frame-time or game-quality improvement is claimed;
- dependency declarations are synthetic and trusted in this phase;
- no topology, transfer, recompute or migration cost is optimized yet;
- no MVCA authority semantics are changed.

## Next falsifier

`FR-P9-002` should add a measured resource topology and placement layer:

```text
semantic sufficiency
        +
RAM / SSD / peer / compute topology
        +
transfer + migration + recompute cost
        -> physical realization plan
```

The critical adversary will be a stale startup plan. After materialization or observation changes the actual resource state, the planner must re-observe and re-plan instead of assuming the original placement is still optimal.

This directly tests the lesson exposed by Strata v0.1.39's RAM-budget refill correction.

## Claim ceiling

`SYNTHETIC_DECLARED_DEPENDENCY_FIXTURE_ONLY_NO_PHYSICAL_RAM_OR_PCG_PERFORMANCE_CLAIM`
