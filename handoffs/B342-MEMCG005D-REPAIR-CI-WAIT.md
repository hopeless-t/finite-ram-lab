# Bounce Handoff

> **Bounce ID:** B342
> **Status:** EXTERNAL_WAIT / MEMCG-005D REPAIR CI IN PROGRESS

Repair:
`c89fec2940537f610ee517885c1d9e813d79f3c6`

Repair CI:
`36552762177`

Single B342 status read:
`in_progress`

No second read was performed.

Repair scope:
remove unaligned `mmap.flush(offset,4)` calls from shared-latch writes.

Scientific design unchanged.

Previous scientific run:
`36552551097 = infrastructure failure`

No scientific result was produced.

Next fresh bounce:
- read CI `36552762177` exactly once;
- success -> create a new explicit MEMCG-005D launch marker and run;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
