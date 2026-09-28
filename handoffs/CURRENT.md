# CURRENT

> **Latest bounce:** B291
> **Stage:** MATH-001 HOSTED RUN + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## MATH-001

Exact launch commit:

`8ba7be304522c2a2653b99e858b5e7671281d071`

Scientific run:

`36453581737`

Single B291 read:

`in_progress`

Do not poll again in this bounce.

## Scientific question

Does Q=64 dominate competing quantization models not only by fit, but by:
- minimum description length;
- held-out prediction;
- reset-aware full-sequence residual?

Decision space:
- MODEL64_WINS
- OTHER_Q_WINS
- MIXED_MODEL

## Accepted input

MEMCG-001:
- 4/4 touch blocks show +64-page charge jumps;
- 0/4 controls show non-zero jumps;
- block2 retains Q64 on both sides of one negative discontinuity with a phase reset.

## Next fresh-bounce action

Read `36453581737` exactly once.

- success -> fetch artifact once and canonicalize MATH-001;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

If MODEL64_WINS, only then freeze the CPU-migration causal perturbation study.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
