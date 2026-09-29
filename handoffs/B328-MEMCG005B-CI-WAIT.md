# Bounce Handoff

> **Bounce ID:** B328
> **Status:** EXTERNAL_WAIT / MEMCG-005B IMPLEMENTATION CI QUEUED

Implementation:
`4d899453a4ffaf8aaaf68f285ede6ea1e9e1ae1b`

Ordinary CI:
`36547079561`

Single B328 status read:
`queued`

No second read was performed.

MEMCG-005B:
- three CPU roles C/P/S;
- workers start zero-touch on P;
- no participant touches S before insertion;
- insertion = MIGRATE P->S then first S TOUCH_ONE;
- 14 verified wash insertions before target;
- independent m={0,5,6,7,8};
- one-shot target probe.

No launch marker exists.

Next fresh bounce:
- read CI `36547079561` exactly once;
- success -> explicit MEMCG-005B launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
