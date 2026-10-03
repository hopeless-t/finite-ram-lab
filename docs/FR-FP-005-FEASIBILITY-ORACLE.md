# FR-FP-005 — Predictive residency feasibility oracle

Status: **SYNTHETIC ROUTING CANDIDATE**

Parent: **FR-FP-004**

## Why

FR-FP-004 produced a phase map.

Reading a phase map manually on every research bounce recreates decision
friction.

FR-FP-005 compiles the frozen phase geometry into a small routing oracle.

Input:

    transfer lead
    hot budget

Output:

    policy-value region
    simple-policy sufficiency
    predictor-model gap
    transfer-surface capability gap

plus a stop / continue signal for policy research.

## Routes

### PREDICTION_SAVES_IO

Route:

    POLICY_VALUE_REGION
    -> OPTIMIZE_PREDICTIVE_POLICY

Policy search remains open because the phase map already proves a zero-OOM
predictive solution with material I/O advantage.

### PREDICTION_HAS_NO_MATERIAL_IO_ADVANTAGE

Route:

    SIMPLE_POLICY_SUFFICIENT
    -> STOP_PREDICTOR_TUNING_USE_SIMPLE_POLICY

This is a research stop condition.

A more complex predictor is not justified when it does not buy material I/O
value in the frozen phase cell.

### NO_ZERO_OOM_PREDICTIVE_CANDIDATE

Route:

    PREDICTOR_MODEL_GAP
    -> IMPROVE_PREDICTOR_OR_POLICY_FAMILY

Always-preemptive is feasible, so the physical transfer surface is not yet the
binding failure.

### DEADLINE_INFEASIBLE

Route:

    TRANSFER_SURFACE_CAPABILITY_GAP
    -> CHANGE_CAPACITY_BANDWIDTH_STATE_SIZE_OR_RECLAIM_TIMING

This is the critical stop rule.

If even always-preemptive transfer cannot meet the deadline, spending more
research budget on policy tuning attacks the wrong layer.

## No interpolation outside evidence

If a lead or budget is outside the frozen FR-FP-004 grid, the oracle returns:

    OUT_OF_CALIBRATION

It does not guess or interpolate.

The next step is new measurement.

## North-Star bridge

The oracle is intentionally compatible with the earlier gap-selector language.

The deadline-infeasible phase maps to a capability gap.

The no-zero-OOM-predictor phase maps to a model/policy gap.

The policy-value region keeps optimization open.

The simple-policy region stops new policy research.

This lets the North-Star selector avoid both:

- mechanism sprawl in already-solvable regions;
- policy sprawl in physically impossible regions.

## Claim ceiling

**SYNTHETIC_PHASE_MAP_ROUTING_ORACLE_ONLY**
