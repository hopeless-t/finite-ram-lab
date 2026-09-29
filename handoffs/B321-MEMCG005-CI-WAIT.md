# Bounce Handoff

> **Bounce ID:** B321
> **Status:** EXTERNAL_WAIT / MEMCG-005 IMPLEMENTATION CI QUEUED

Implementation:
`81118055839291dc3f939c0b7ff01ca7080cf343`

Ordinary CI:
`36544481855`

Single B321 status read:
`queued`

No second read was performed.

MEMCG-005 implements:
- prestarted 16-worker replicas;
- observed-Q64 + 63-touch EMPTY normalization;
- verified +64 measured insertions;
- target one-shot probe;
- independent m={0,5,6,7,8} replicas;
- sparse K=1..9 model competition and equivalence classes.

No launch marker exists.

Next fresh bounce:
- read CI `36544481855` exactly once;
- success -> explicit MEMCG-005 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
