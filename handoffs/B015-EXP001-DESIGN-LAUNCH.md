# Bounce Handoff

> **Bounce ID:** B015  
> **Status:** COMPLETE / COMPUTE LAUNCHED

## Objective

Use Monte Carlo to choose the smallest blocked design for the residency-identity causal experiment.

## Pseudo-Council convergence

- compare HOT_EVICT versus COLD_EVICT under low pressure;
- reclaim the same 16 MiB amount in both arms;
- always retouch the semantic HOT region;
- runner identity is the top-level replication unit;
- final analysis will use exact block sign-flip inference;
- design Monte Carlo must use the same inferential structure.

## Candidate designs

- D1: 6 blocks × 2 repeats/arm = 24 trials;
- D2: 8 blocks × 2 repeats/arm = 32 trials;
- D3: 8 blocks × 3 repeats/arm = 48 trials;
- D4: 12 blocks × 2 repeats/arm = 48 trials.

## Workflow

- run: `36228047531`
- commit: `4b69861d23e62380bcd605cc5e1c692d101ced2f`

## Next recommended bounce

> Read the design Monte Carlo, freeze one design without changing the causal question, and write the EXP-001 execution spec.

## Authority boundary

Design power simulation is not evidence that residency identity affects performance.
