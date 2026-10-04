# FR-META-025 — Decision-directed model maintenance

Status: **CROSS-PLANE PRUNING ADAPTER CANDIDATE**

Parent: **FR-META-024**

Evidence:
- FR-FP-052 / PR #177
- FR-FP-053 / PR #178

## New proof adapter

The existing resident capsule remains:

    PRUNE_PROVEN_DECISION_IRRELEVANT_WORK

No new skill is added.

The model-maintenance adapter derives the same normalized proof only when:

    migration_model_refit_question = true
    structural_migration_model_qualified = true
    current_run_direction_scaling_holdout_improves = true
    scaled_optimal_path_changed = false

Then:

    decision_irrelevance_proven = true
    skip_preserves_admissible_decision = true

and the generic capsule prunes structural refit.

## Fail closed

If the calibrated optimal path changes:

    scaled_optimal_path_changed = true

the adapter does not derive decision irrelevance.

Structural model maintenance remains available.

Likewise, missing qualification or missing holdout improvement does not select
the pruning capsule.

## Why this is a new plane

Earlier adapters prune:

1. reuse monitoring;
2. a second calibration measurement;
3. physical placement actuation.

FR-FP-053 is different.

It prunes **structural model retraining** while retaining a smaller current-run
calibration state.

The rule is therefore now reproduced across observation, measurement,
actuation and model-maintenance planes.

## Resident budget

The proof adapter is deterministic code around the existing skill.

Resident skill count must remain:

    18

The frozen catalog budget remains:

    < 30% of source-history characters

No budget relaxation is allowed.

## Claim ceiling

**CROSS_PLANE_DECISION_RELEVANCE_PRUNING_EXTENDED_TO_FP053_MIGRATION_MODEL_MAINTENANCE_ONLY**
