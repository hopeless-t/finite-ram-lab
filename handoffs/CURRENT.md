# CURRENT

> **Latest bounce:** B351
> **Stage:** MEMCG-005E REJECTED / MEMCG-005F REMOTE-LOW DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## MEMCG-005E canonical result

Run:
`36556517823`

Decision:
`REJECT_BASELINE_GATE`

Canonical:
`docs/MEMCG-005E-RESULT.md`

Key result:
- pooled LOW: 89/160 Q64
- pooled HIGH: 9/96 Q64
- LOCAL_P: 0/128 Q64
- REMOTE_S LOW: 89/90 Q64
- REMOTE_S HIGH: 9/38 Q64

Frozen threshold remains:
`pre_current_pages <= 110`

## MEMCG-005F

Design:
`docs/MEMCG-005F-REMOTE-LOW-ADMISSION-GATE-v1.md`

Primary composite gate:
`REMOTE_LOW := startup P, measured S != P, pre_current_pages <= 110`

Scale:
64 identities per block x 4 blocks = 256 probes.

No K7 inference.

## Next fresh-bounce action

Implement MEMCG-005F only.

Do not launch during implementation.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
