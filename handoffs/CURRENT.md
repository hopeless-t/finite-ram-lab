# CURRENT

> **Latest bounce:** B305
> **Stage:** MEMCG-003 HOSTED RUN + PMNDRS MATH LENS FROZEN
> **Turn stop reason:** EXTERNAL_WAIT

## MEMCG-003

Implementation:
`b64f32ad3b38d4a6ca8bdfda36e4c12fe62d5569`

Launch:
`6cb688d7c8578ce95e217e83adcb7249a3555efa`

Two scientific runs materialized for the exact launch head.

Canonicalization rule fixed before reading results:
- canonical: `36459951576` (first materialized run)
- duplicate/noncanonical: `36459972685`

Do not select between runs based on results.

Single discovery state:
- canonical run: in_progress
- duplicate run: queued

Do not poll again in this bounce.

## pmndrs/math

Pinned source:
`pmndrs/math@98762395c1f34d7d594d31165e8005fd6915c431`

Secondary design:
`docs/MATH-002-PMNDRS-GEOMETRIC-LENS-v1.md`

Use after canonical MEMCG-003 result:
- quickhull2 response/control envelopes
- quickhull3 secondary envelope
- seeded mulberry32 permutation null
- geometric transition score near m in {6,7,8}

This geometry lens is secondary and cannot override the preregistered MEMCG-003 threshold/Bayesian decision.

## Next fresh-bounce action

Read canonical run `36459951576` exactly once.

- success -> fetch canonical aggregate once, analyze MEMCG-003, then run/implement the frozen pmndrs/math secondary lens on that canonical evidence;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Ignore duplicate run for scientific model selection.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
