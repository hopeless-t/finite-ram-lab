# Bounce Handoff

> **Bounce ID:** B295
> **Status:** EXTERNAL_WAIT / MEMCG-002 IMPLEMENTATION CI QUEUED

Exact implementation commit:

`19776a4c50412d5b929f8b1130f83b22e2345f04`

Ordinary CI:

`36454940719`

Single status read in B295:

`queued`

No second read was performed.

MEMCG-002 is implemented but not launched.

Causal intervention:
- FIXED_TOUCH
- MIGRATE_TOUCH A->B after step128
- ROUNDTRIP_TOUCH A->B after128, B->A after192
- ROUNDTRIP_CONTROL

Key predictions:
- first B-side +64 charge within 1-2 touches;
- B-side Q64 spacing;
- old A modulo64 phase restored on roundtrip;
- migration-only control produces no positive events.

Next fresh bounce:
- read CI `36454940719` exactly once;
- success -> explicit MEMCG-002 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
No memory-control policy.
