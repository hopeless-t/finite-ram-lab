# Bounce Handoff

> **Bounce ID:** B322
> **Status:** MEMCG-005 EXPLICIT HOSTED LAUNCH

Implementation:
`81118055839291dc3f939c0b7ff01ca7080cf343`

CI:
`36544481855 = success`

Exact launch commit:
`b8c1cfbf4e54fef37a314fbe629fceef4734ff0b`

Scientific design:
- prestart 16 worker identities;
- normalize every identity to EMPTY by observed +64 then 63 consumptions;
- verify wash/target/challenger insertion by fresh +64;
- independent replicas m={0,5,6,7,8};
- one-shot target probe.

Source K7 signature:
- m0/5/6 PRESENT
- m7/8 ABSENT

Next: discover/read exact-head MEMCG-005 run once.

Hosted research only.
No local-PC execution.
