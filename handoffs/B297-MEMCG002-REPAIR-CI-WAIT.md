# Bounce Handoff

> **Bounce ID:** B297
> **Status:** EXTERNAL_WAIT / MEMCG-002 REPAIR CI IN PROGRESS

Analyzer repair commit:
`3e563db223c80938a09a8a1567c8b9fe4e5836d4`

Repair CI:
`36455336164`

Single B297 status read:
`in_progress`

No second read was performed.

Repair scope:
- MIGRATE_TOUCH B-side spans step129..256;
- ROUNDTRIP arms keep B-side step129..192.

No scientific design or preregistered criterion changed.
No MEMCG-002 launch marker exists.

Next fresh bounce:
- read CI `36455336164` exactly once;
- success -> explicit MEMCG-002 hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
No memory-control policy.
