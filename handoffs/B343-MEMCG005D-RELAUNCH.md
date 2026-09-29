# Bounce Handoff

> **Bounce ID:** B343
> **Status:** MEMCG-005D EXPLICIT RELAUNCH AFTER RUNTIME REPAIR

Implementation:
`bac7f0babe87a7350f81ea37113b3798b512ca7d`

Runtime repair:
`c89fec2940537f610ee517885c1d9e813d79f3c6`

Repair CI:
`36552762177 = success`

Exact relaunch commit:
`098607e7b8f76377841a718799d896f50a0bef12`

Previous run:
`36552551097 = infrastructure failure only`

Scientific design unchanged:
- SELF_ATOMIC: worker self-migration then immediate touch;
- EXTERNAL_ATOMIC: controller external migration, mid current sample, shared GO, immediate touch;
- 23 identities per arm per block;
- 4 blocks;
- 184 probes.

Next: discover/read exact-head MEMCG-005D run once.

Hosted research only.
No local-PC execution.
