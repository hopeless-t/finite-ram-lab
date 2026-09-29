# CURRENT

> **Latest bounce:** B340
> **Stage:** MEMCG-005D EXPLICIT HOSTED LAUNCH
> **Turn stop reason:** RUN_DISCOVERY_PENDING

## MEMCG-005C accepted result

Canonical:
`909b554048e4e269ebb644c8533857468cae8296`

Decision:
`REJECT_ATOMIC_PATH`

## MEMCG-005D

Implementation:
`bac7f0babe87a7350f81ea37113b3798b512ca7d`

Implementation CI:
`36552457074 = success`

Launch:
`f4ca08442547142f1aaf0d0113f0653da3d7ee09`

A/B:
- SELF_ATOMIC = worker self-migration then immediate touch;
- EXTERNAL_ATOMIC = controller external migration + mid current + shared GO + immediate touch.

23 identities per arm per block.
4 blocks.
184 probes.

EXTERNAL records migration delta and touch delta separately.

## Next fresh-bounce action

Discover/read exact-head MEMCG-005D workflow once.

- pending/in_progress -> record run id, EXTERNAL_WAIT;
- success -> fetch aggregate once and canonicalize;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
