# FR-META-022 — Physical placement adapter for decision-relevance pruning

Status: **CROSS-PLANE PHYSICAL ADAPTER CANDIDATE**

Parent: **FR-META-021**

Evidence:
- reuse monitoring: FR-FP-031 / PR #151, FR-FP-032 / PR #152
- calibration measurement: FR-FP-033 / PR #154
- physical placement: FR-FP-038 / PR #160, FR-FP-039 / PR #161

## Third independent plane

FR-FP-039 physically qualified an online evidence update where semantic state
values changed but the optimal WARM set did not.

Observed physical action:

    0 tier actions

and the full physical resident snapshot remained unchanged.

That is the same normalized invariant already compiled for two other planes:

    decision_irrelevance_proven = true
    skip_preserves_admissible_decision = true

## Physical-placement adapter

Trigger facts:

    physical_placement_update_question = true
    multistate_allocator_qualified = true
    optimal_warm_set_changed = false

Derived proof:

    decision_irrelevance_proven = true
    skip_preserves_admissible_decision = true

Action:

    PRUNE_PROVEN_DECISION_IRRELEVANT_WORK

If the optimal WARM set changes, fail closed and retain actuation.

## No skill-count growth

Do not create a placement-specific LLM-facing skill.

The existing resident capsule remains:

    PRUNE_PROVEN_DECISION_IRRELEVANT_WORK

Only deterministic domain proof expands.

Resident skill count remains 17.

## Generalization status

The invariant now has independent qualified support in:

1. observation/control monitoring;
2. physical calibration measurement;
3. physical multi-state actuation.

This is stronger evidence for a general meta-meta pruning invariant, but the
authority boundary remains unchanged: pruning can only remove proven
decision-irrelevant work.

## Claim ceiling

**CROSS_PLANE_DECISION_RELEVANCE_PRUNING_FOR_REUSE_MONITORING_CALIBRATION_AND_PHYSICAL_PLACEMENT_ONLY**
