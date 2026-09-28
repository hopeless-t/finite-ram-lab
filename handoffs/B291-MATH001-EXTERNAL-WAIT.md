# Bounce Handoff

> **Bounce ID:** B291
> **Status:** EXTERNAL_WAIT / MATH-001 HOSTED RUN IN PROGRESS

Exact launch commit:

`8ba7be304522c2a2653b99e858b5e7671281d071`

Scientific run:

`36453581737`

Single status read in B291:

`in_progress`

No second read was performed.

## What is being decided

MATH-001 is testing whether Q=64 is merely a visually attractive divisor or the simplest predictive model.

Competition:
- Q = 1,2,4,8,16,32,64,128
- stationary staircase
- reset-aware staircase
- arbitrary events
- linear comparator

Primary evidence:
- reset-aware full-sequence residual
- combinatorial MDL
- leave-one-block-out predictive F1

A MODEL64_WINS result requires:
- minimum reset-aware SSE at Q64;
- minimum MDL at Q64;
- every training fold selects Q64;
- held-out F1 = 1.0 in every fold;
- no competing control pattern.

## If MODEL64_WINS

Next physical causal study should test the hidden per-CPU stock interpretation by deliberately perturbing CPU affinity/migration while preserving the same cgroup and one-page touch sequence.

Do not freeze or launch that causal experiment until MATH-001 completes.

## Next fresh-bounce action

Read run `36453581737` exactly once.

- success -> fetch artifact once, canonicalize model-competition result, then freeze the causal CPU-state perturbation study;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
No memory-control policy.
