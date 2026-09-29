# Bounce Handoff

> **Bounce ID:** B326
> **Status:** COMPLETE / MEMCG-005B THREE-CPU DESIGN FROZEN

Repair:
- C controller
- P startup/prep
- S stock-test
- workers never touch S before measured insertion
- insertion = MIGRATE S + first TOUCH_ONE, required +64
- 14 distinct washes before target to wash out unknown initial 7-slot occupancy/drain_idx
- target one-shot probe after m={0,5,6,7,8}

Source prediction remains:
0/5/6 PRESENT, 7/8 ABSENT.

Next:
implement only; do not launch during implementation bounce.

Hosted research only.
