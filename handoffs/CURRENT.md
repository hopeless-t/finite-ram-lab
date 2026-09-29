# CURRENT

> Latest bounce: B360
> Stage: MEMCG-005G-A COMPLETE / MEMCG-005G-B DESIGN FROZEN
> Stop: READY_FOR_IMPLEMENTATION

## MEMCG-005G-A

Run:
`36563233676`

Decision:
`INCONCLUSIVE`

Canonical:
`docs/MEMCG-005G-A-RESULT.md`

Primary:
- EARLY 9/102 failure =8.82%
- STEADY 19/304 =6.25%
- Fisher one-sided p=.248
- BF10 two-rate/shared=.113

Biopsy:
- 28 failures
- 22 depth1
- deep tail 14,34,45,45,47,48
- all recovered Q64 by touch65
- no censoring

Cross-experiment caution:
005F failure 2/123=1.63%
005G-A failure 28/406=6.90%

Potential confounds:
- max-pages 8 ->70
- 4 hosted blocks ->24 independent hosted blocks

## MEMCG-005G-B

Design:
`docs/MEMCG-005G-B-BIOPSY-FOOTPRINT-CONTROL-v1.md`

CAP8 vs CAP70, identical first-touch path, alternating within runner.
16 blocks x64 candidates.

No launch marker exists.

## Next fresh bounce

Implement MEMCG-005G-B only.
Do not launch during implementation.

Hosted research only.
No local-PC execution.
