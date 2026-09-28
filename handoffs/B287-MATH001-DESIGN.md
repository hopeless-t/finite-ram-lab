# Bounce Handoff

> **Bounce ID:** B287
> **Status:** COMPLETE / MATH-001 MODEL-COMPETITION DESIGN FROZEN

Input:
`evidence/MEMCG-001/event-sequence-v1.json`

Candidate models:
- NULL
- LINEAR
- STAIRCASE(Q)
- RESET_STAIRCASE(Q)
- ARBITRARY_EVENTS

Q panel:
`1,2,4,8,16,32,64,128`

Primary competition:
- full-sequence residual
- combinatorial MDL
- leave-one-block-out prediction

Secondary:
- phase coherence / spectral diagnostic
- simple combinatorial null sanity check

Decision can select Q64, another Q, or MIXED_MODEL.

Next: implement only. Do not launch in implementation bounce.

Hosted research only.
