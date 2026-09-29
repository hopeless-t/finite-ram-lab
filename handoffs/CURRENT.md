# CURRENT

> **Latest bounce:** B310
> **Stage:** MEMCG-003B HOSTED RUN + MATH-002 SIDECAR IMPLEMENTED
> **Turn stop reason:** EXTERNAL_WAIT

## MEMCG-003B

Exact launch:
`5987143f7aaced18165289c76969b6ff386895db`

Scientific run:
`36527502073`

Single B309 discovery:
`in_progress`

Do not read again in this bounce.

## MATH-002

Pinned:
`pmndrs/math@98762395c1f34d7d594d31165e8005fd6915c431`

Implemented but not launched:
- QuickHull2 distinct/control envelopes
- per-block hulls
- fixed-seed mulberry32
- 100,000 permutation null

The workflow requires:
`evidence/MEMCG-003B/canonical/summary.json`

Therefore MATH-002 cannot run before the primary canonical result is committed.

## Next fresh-bounce action

Read run `36527502073` exactly once.

- success -> fetch aggregate once, canonicalize MEMCG-003B primary result, prepare canonical summary, then launch MATH-002;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
