# Bounce Handoff

> **Bounce ID:** B346
> **Status:** MEMCG-005D CANONICALIZED / MEMCG-005E DESIGN FROZEN

MEMCG-005D:
- run 36553495930
- decision REJECT_EXTERNAL_PATH
- SELF 68/92 Q64
- EXTERNAL 63/92 Q64
- EXTERNAL migration delta 0 in 92/92
- all failures zero-delta

Post-hoc predictor:
- pre_current <=110 pages:
  - SELF 46/46 Q64
  - EXTERNAL 38/39 Q64

MEMCG-005E prospectively freezes threshold <=110 pages and compares LOCAL_P vs REMOTE_S.

Next:
implement only; do not launch during implementation.

Hosted research only.
