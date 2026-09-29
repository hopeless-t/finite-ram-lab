# Bounce Handoff

> **Bounce ID:** B351
> **Status:** MEMCG-005E CANONICALIZED / MEMCG-005F DESIGN FROZEN

MEMCG-005E run:
`36556517823`

Decision:
`REJECT_BASELINE_GATE`

Pooled:
- LOW 89/160 Q64
- HIGH 9/96 Q64

CPU split:
- LOCAL_P: 0/128 Q64
- REMOTE_S LOW: 89/90 Q64
- REMOTE_S HIGH: 9/38 Q64

REMOTE_S LOW by block:
16/16, 26/26, 23/23, 24/25.

Accepted lesson:
baseline is not sufficient without CPU locality.

MEMCG-005F freezes the composite REMOTE_LOW gate:
remote CPU S plus pre_current<=110 pages.

Next:
implement only; do not launch during implementation.

Hosted research only.
