# CURRENT

> **Latest bounce:** B344
> **Stage:** MEMCG-005D REPAIRED HOSTED RUN + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## MEMCG-005C accepted result

Canonical:
`909b554048e4e269ebb644c8533857468cae8296`

Decision:
`REJECT_ATOMIC_PATH`

ATOMIC:
- 69/92 Q64
- 23 zero-delta failures

TWO_STEP:
- 77/92 Q64
- 15 zero-delta failures

Receipt-I/O hypothesis rejected.

## MEMCG-005D

Implementation:
`bac7f0babe87a7350f81ea37113b3798b512ca7d`

Runtime repair:
`c89fec2940537f610ee517885c1d9e813d79f3c6`

Repair CI:
`36552762177 = success`

Exact relaunch:
`098607e7b8f76377841a718799d896f50a0bef12`

Scientific run:
`36553495930`

Single B344 read:
`in_progress`

Do not poll again in this bounce.

A/B:
- SELF_ATOMIC = worker self-migration;
- EXTERNAL_ATOMIC = controller-driven migration + pre/mid/post memory.current decomposition + shared GO.

23 identities per arm per block.
4 blocks.
184 probes.

## Next fresh-bounce action

Read run `36553495930` exactly once.

- success -> fetch aggregate once, compare external vs self first-touch failure rates and migration/touch deltas, canonicalize;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
