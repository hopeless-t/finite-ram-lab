# Bounce Handoff

> **Bounce ID:** B324
> **Status:** EXTERNAL_WAIT / MEMCG-005 HOSTED RUN IN PROGRESS

Scientific run:
`36545631176`

Single B324 status read:
`in_progress`

No second read was performed.

Scientific design:
- every identity normalized to EMPTY by observed +64 then 63 consumptions;
- every measured wash/target/challenger insertion must produce fresh +64;
- independent m={0,5,6,7,8};
- one-shot target probe.

Source K7 signature:
- m0/5/6 PRESENT
- m7/8 ABSENT

Next fresh bounce:
- read run `36545631176` exactly once;
- success -> fetch aggregate once, inspect validity matrix and boundary signature, canonicalize;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Hosted research only.
No local-PC execution.
