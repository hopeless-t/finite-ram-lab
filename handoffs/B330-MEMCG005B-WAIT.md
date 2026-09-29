# Bounce Handoff

> **Bounce ID:** B330
> **Status:** EXTERNAL_WAIT / MEMCG-005B HOSTED RUN IN PROGRESS

Exact launch commit:
`73baca88f9701c1d819cdb9a11da38d033669aff`

Scientific run:
`36547649316`

Single B330 status read:
`in_progress`

No second read was performed.

Scientific design:
- C controller;
- P startup/prep;
- S stock-test;
- no participant touches S before measured insertion;
- 14 verified wash insertions before target;
- independent m={0,5,6,7,8};
- one-shot target probe.

Source K7 signature:
- m0/5/6 PRESENT
- m7/8 ABSENT

Next fresh bounce:
- read run `36547649316` exactly once;
- success -> fetch aggregate once, inspect validity matrix and boundary signature, canonicalize;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
