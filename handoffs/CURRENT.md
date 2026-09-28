# CURRENT

> **Latest bounce:** B287
> **Stage:** MATH-001 MODEL COMPETITION DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## MEMCG-001

Canonical verdict:
`SUPPORT_H64`

But original best-Q scoring has divisor aliasing.

## MATH-001

Frozen candidate models:
- NULL
- LINEAR
- STAIRCASE(Q)
- RESET_STAIRCASE(Q)
- ARBITRARY_EVENTS

Q:
`1,2,4,8,16,32,64,128`

Primary metrics:
- full-sequence RMSE/MAE
- combinatorial MDL position code
- MDL savings vs arbitrary positions
- leave-one-block-out predictive precision/recall/F1

Reset-aware segments are defined only by observed negative memory.current discontinuities.

Decision:
- MODEL64_WINS
- OTHER_Q_WINS
- MIXED_MODEL

Design:
`docs/MATH-001-MODEL-COMPETITION-v1.md`

## Next fresh-bounce action

Implement:
- deterministic analyzer
- markdown renderer
- tests for divisor alias rejection
- hosted workflow gated by `launch/MATH-001-v1.txt`

Do not launch during implementation.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
