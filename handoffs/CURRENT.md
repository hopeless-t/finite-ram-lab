# CURRENT

> **Latest bounce:** B288
> **Stage:** MATH-001 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## MATH-001 implementation

Files:
- `src/finite_ram_lab/math001_model_competition.py`
- `.github/workflows/math-001-model-competition.yml`
- `tests/test_math001_model_competition.py`

Input:
`evidence/MEMCG-001/event-sequence-v1.json`

Competition:
- LINEAR
- STAIRCASE(Q)
- RESET_STAIRCASE(Q)
- ARBITRARY_EVENTS

Q:
`1,2,4,8,16,32,64,128`

Scores:
- full sequence SSE/RMSE
- combinatorial MDL
- leave-one-block-out prediction
- divisor false-prediction penalty
- reset-aware phase segmentation
- spectral coherence diagnostic

No launch marker exists.

## Next fresh-bounce action

Discover/read B288 ordinary CI exactly once.

- success -> explicit MATH-001 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
