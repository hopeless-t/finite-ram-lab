# CURRENT

> **Latest bounce:** B335
> **Stage:** MEMCG-005C REPAIR CI + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## MEMCG-005C

Implementation:
`82515df80b1cde1d9b9732510c3abf1454b2aa91`

Initial CI:
`36550320654 = failure`

Exposed failure:
synthetic support fixture created 91 failures instead of 1.

Repair:
`57d1c0767f3fd3fbeef8902c78cf6a7bc80b3143`

Repair CI:
`36550984469`

Single B335 read:
`in_progress`

Do not poll again in this bounce.

Scientific design unchanged:
- TWO_STEP old path;
- ATOMIC migrate + immediate measured touch before receipt I/O;
- 23 identities per arm per block;
- 4 blocks;
- 184 first-touch probes total.

No launch marker exists.

## Next fresh-bounce action

Read CI `36550984469` exactly once.

- success -> explicit MEMCG-005C hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
