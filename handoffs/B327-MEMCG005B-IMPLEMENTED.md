# Bounce Handoff

> **Bounce ID:** B327
> **Status:** COMPLETE / MEMCG-005B IMPLEMENTED / NOT LAUNCHED

Implemented:
- zero-touch worker with MIGRATE command;
- controller/prep/stock three-CPU role split;
- workers start only on P;
- each measured insertion is MIGRATE P->S then first S TOUCH_ONE;
- 14 verified wash insertions before target;
- independent m={0,5,6,7,8};
- one-shot target probe;
- K=1..9 analyzer;
- synthetic tests and hosted workflow.

No launch marker exists.

Next:
read ordinary CI once.

Hosted research only.
