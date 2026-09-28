# Bounce Handoff

> **Bounce ID:** B306
> **Status:** MEMCG-003 CANONICALIZED / MEMCG-003B REPAIR DESIGN FROZEN

Canonical MEMCG-003 run:
`36459951576`

Primary decision:
`REJECT_K7_SLOT_MODEL`

Thresholds:
`[2,1,4,2]`

But controls also generated fresh +64 target recharges.

Root measurement issue:
the repeated target probe consumed one cached stock page per observation.

Stock-drop-only diagnostic:
- distinct: [3,2,6,7]
- six-only: [5,None,1,4]
- same-memcg: [None,None,None,None]
- no-churn: [None,None,7,None]

Repair frozen as MEMCG-003B:
- passive target-current observation only during churn;
- one final target touch after sequence;
- orchestrator pinned to separate CPU C;
- all cache workers pinned to stock CPU S.

Next: implement MEMCG-003B only. Do not launch during implementation.

MATH-002 remains secondary and cannot rescue contaminated primary data.
