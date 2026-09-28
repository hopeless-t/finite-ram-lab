# CURRENT

> **Latest bounce:** B286
> **Stage:** MEMCG-001 PASS / SUPPORT_H64 / READY FOR MODEL COMPETITION
> **Turn stop reason:** READY_FOR_MATH_DESIGN

## MEMCG-001

Run:
`36449072026`

Result:
`SUPPORT_H64`

- touch support: 4/4
- control support: 0/4
- positive jump magnitude: exactly 64 pages

Three blocks are exact stationary 64-page staircases.

Block2 contains one negative discontinuity at step173. Before and after it, the positive jumps form exact 64-page lattices with different phases.

Canonical result:
`docs/MEMCG-001-RESULT.md`

Compact event evidence:
`evidence/MEMCG-001/event-sequence-v1.json`

## Next fresh-bounce action

Freeze MATH-001 model competition.

Candidate models:
- page-linear
- stationary staircase Q
- reset-aware staircase Q
- arbitrary events
- null/control

Candidate Q:
`1,2,4,8,16,32,64,128`

Primary comparison:
- MDL / combinatorial description length
- leave-one-block-out predictive F1
- full-sequence residual
- reset-aware segmentation at observed negative discontinuities

Secondary:
- periodogram / spectral power only as supporting evidence

Goal:
select the simplest predictive model without privileging Q64.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
