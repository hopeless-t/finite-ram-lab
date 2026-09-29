# CURRENT

> **Latest bounce:** B337
> **Stage:** MEMCG-005C HOSTED RUN + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## MEMCG-005C

Implementation:
`82515df80b1cde1d9b9732510c3abf1454b2aa91`

Fixture repair:
`57d1c0767f3fd3fbeef8902c78cf6a7bc80b3143`

Repair CI:
`36550984469 = success`

Launch:
`d50af917577493dc457aa0439a192ab90e5f90a1`

Scientific run:
`36551226475`

Single B337 read:
`in_progress`

Do not poll again in this bounce.

Scientific A/B:
- TWO_STEP old migrate-receipt path;
- ATOMIC migrate + immediate measured touch before receipt I/O;
- 23 identities per arm per block;
- 4 blocks;
- 184 first-touch probes.

## Next fresh-bounce action

Read run `36551226475` exactly once.

- success -> fetch aggregate once, compare atomic vs two-step failure rates, canonicalize;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
