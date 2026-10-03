# FR-FP-005 Receipt

Status: **PASS / SYNTHETIC FEASIBILITY ORACLE QUALIFIED**

Parent: **FR-FP-004**

- workflow run: 37143110512
- job: 111261454023
- execution head: bd8c0b7375f3113c9a0933355cec7fce56085e05

Qualified routes:

- PREDICTION_SAVES_IO
  -> POLICY_VALUE_REGION
  -> continue predictive-policy optimization

- PREDICTION_HAS_NO_MATERIAL_IO_ADVANTAGE
  -> SIMPLE_POLICY_SUFFICIENT
  -> stop predictor tuning

- NO_ZERO_OOM_PREDICTIVE_CANDIDATE
  -> PREDICTOR_MODEL_GAP
  -> improve predictor / policy family

- DEADLINE_INFEASIBLE
  -> TRANSFER_SURFACE_CAPABILITY_GAP
  -> stop policy search and change capacity / bandwidth / state size /
     reclaimability timing

Out-of-calibration lead/budget inputs fail closed to new measurement rather than
interpolation.

Decision:

**ROUTE_POLICY_RESEARCH_ONLY_INSIDE_THE_FEASIBLE_VALUE_REGION**

Claim ceiling:

**SYNTHETIC_PHASE_MAP_ROUTING_ORACLE_ONLY**
