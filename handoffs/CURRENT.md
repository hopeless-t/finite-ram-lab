# CURRENT

> **Latest bounce:** B343
> **Stage:** MEMCG-005D EXPLICIT RELAUNCH
> **Turn stop reason:** RUN_DISCOVERY_PENDING

## MEMCG-005C accepted result

Canonical:
`909b554048e4e269ebb644c8533857468cae8296`

Decision:
`REJECT_ATOMIC_PATH`

## MEMCG-005D

Implementation:
`bac7f0babe87a7350f81ea37113b3798b512ca7d`

Runtime repair:
`c89fec2940537f610ee517885c1d9e813d79f3c6`

Repair CI:
`36552762177 = success`

Previous scientific run:
`36552551097 = infrastructure failure only`

Exact relaunch:
`098607e7b8f76377841a718799d896f50a0bef12`

A/B unchanged:
- SELF_ATOMIC worker self-migration;
- EXTERNAL_ATOMIC controller external migration + mid current + shared GO.

23 identities per arm per block.
4 blocks.
184 probes.

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
