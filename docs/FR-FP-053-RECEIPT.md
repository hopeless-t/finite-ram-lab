# FR-FP-053 Receipt

Status: **PASS / CURRENT-RUN MIGRATION CALIBRATION WITH DECISION-DIRECTED REFIT GATE QUALIFIED**

Parent: **FR-FP-052**

Qualification:
- workflow run: 37223420140
- job: 111498109570
- execution head: aeaa5a48618fbd81e72fe9ecdeff394dfc6f6e56
- new physical runs: 0

Calibration uses only FR-FP-052 JOINT pure-direction transitions.

Current-run multiplicative scales:
- PROMOTE: 0.560647
- EVICT: 1.047721

Held-out validation uses only migration-blind semantic mixed transitions.

Unscaled FP048 model on held-out mixed transitions:
- MAE: 20.0139 ms
- RMSE: 25.9794 ms

Direction-scaled model:
- MAE: 1.5438 ms
- RMSE: 1.8264 ms
- MAE reduction: 92.29%
- maximum relative holdout error: 17.30%

Re-optimizing the complete five-phase FR-FP-051 path with the scaled current-run
cost surface changes:

    0 / 5 placements

All WARM sets remain identical.

Decision:

**KEEP_THE_STRUCTURAL_AFFINE_BYTE_MODEL_AND_SKIP_STRUCTURAL_REFIT_WHEN_LIGHTWEIGHT_CURRENT_RUN_DIRECTION_SCALING_RESTORES_HELDOUT_ERROR_WITHOUT_CHANGING_THE_OPTIMAL_PATH**

Interpretation:

The structural FP048 model was miscalibrated in magnitude on this hosted run,
especially for PROMOTE, but the error did not require structural retraining.

A two-number current-run sufficient state repaired unseen mixed-transition
prediction while preserving the admissible placement path.

Meta consequence:

Model maintenance should be decision-directed.

Prediction error alone is not sufficient evidence for a structural refit when:
1. a cheaper qualified calibration repairs held-out prediction; and
2. the admissible decision remains unchanged.

Claim ceiling:

**CURRENT_RUN_DIRECTION_SCALING_AND_REFIT_SKIP_ON_ONE_FP052_HOSTED_TRACE_ONLY**
