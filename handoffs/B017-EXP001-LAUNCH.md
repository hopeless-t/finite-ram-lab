# Bounce Handoff

> **Bounce ID:** B017  
> **Status:** COMPLETE / COMPUTE LAUNCHED

## Objective

Implement and launch EXP-001 exactly as frozen.

## Completed

- implemented HOT_EVICT / COLD_EVICT workload;
- implemented fidelity checks before primary retouch;
- implemented exact 2^8 block sign-flip analysis;
- implemented cluster-bootstrap latency ratio;
- launched 8 independent hosted-runner blocks.

## Workflow

- run: `36228194951`
- commit: `7af5d74ca1bce2ef7d7c3dd0a7e5eefeeb6d5761`

## Frozen rule

Do not alter arm definitions, fidelity thresholds, or primary inference while the workflow is running.

## Next recommended bounce

> Read the completed evidence with only the frozen analysis and record the causal finding.

## Authority boundary

Launching the intervention is not evidence of a causal effect.
