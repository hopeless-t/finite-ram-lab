# Bounce Handoff

> **Bounce ID:** B344
> **Status:** EXTERNAL_WAIT / MEMCG-005D REPAIRED RUN IN PROGRESS

Repair:
`c89fec2940537f610ee517885c1d9e813d79f3c6`

Repair CI:
`36552762177 = success`

Exact relaunch:
`098607e7b8f76377841a718799d896f50a0bef12`

Scientific run:
`36553495930`

Single B344 status read:
`in_progress`

No second read was performed.

Scientific A/B:
- SELF_ATOMIC: worker self-migration then immediate touch;
- EXTERNAL_ATOMIC: controller external migration, mid current sample, shared GO, immediate touch;
- 23 identities per arm per block;
- 4 blocks;
- 184 probes.

Next fresh bounce:
- read run `36553495930` exactly once;
- success -> fetch aggregate once and canonicalize;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
