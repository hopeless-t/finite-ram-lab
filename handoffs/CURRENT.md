# CURRENT

> **Latest bounce:** B308
> **Stage:** MEMCG-003B IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Canonical MEMCG-003 lesson

MEMCG-003 primary decision:
`REJECT_K7_SLOT_MODEL`

But the repeated target probe itself consumed hidden stock and contaminated controls.

This was preserved as a scientific result rather than repaired post hoc.

## MEMCG-003B

Implementation:
`985d4efe4ebaa2eb877d2ad307bac630279d14d6`

Repairs:
- passive target memory.current observations only;
- zero target touches during challenger sequence;
- one final touch for Q64 recharge confirmation;
- two-CPU isolation: control plane vs stock plane.

Ordinary CI:
`36469054700`

Single B308 read:
`in_progress`

Do not poll again in this bounce.

No launch marker exists.

## pmndrs/math

MATH-002 remains secondary:
- QuickHull response/control geometry
- seeded permutation null
- cannot override primary threshold/Bayes/LOBO result

Run it only after clean MEMCG-003B canonical evidence exists.

## Next fresh-bounce action

Read CI `36469054700` exactly once.

- success -> explicit MEMCG-003B hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
