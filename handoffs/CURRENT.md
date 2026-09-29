# CURRENT

> **Latest bounce:** B346
> **Stage:** MEMCG-005D REJECTED / MEMCG-005E BASELINE DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## MEMCG-005D canonical result

Run:
`36553495930`

Decision:
`REJECT_EXTERNAL_PATH`

SELF_ATOMIC:
- 68/92 Q64
- 24 zero-delta failures

EXTERNAL_ATOMIC:
- 63/92 Q64
- 29 zero-delta failures
- migration delta = 0 for 92/92
- CPU mismatch = 0

Canonical result:
`docs/MEMCG-005D-RESULT.md`

## Prospective next hypothesis

Post-hoc MEMCG-005D signal:

`pre_current_pages <= 110`

predicted:
- SELF 46/46 Q64
- EXTERNAL 38/39 Q64

This threshold is now frozen prospectively.

## MEMCG-005E

Design:
`docs/MEMCG-005E-BASELINE-STRATIFIED-FIRST-TOUCH-v1.md`

Arms:
- LOCAL_P
- REMOTE_S

32 identities per arm per block.
4 blocks.
256 probes.

Primary question:
does LOW baseline prospectively achieve >=95% Q64 and outperform HIGH baseline?

No K7 inference.

## Next fresh-bounce action

Implement MEMCG-005E only.

Do not launch during implementation.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
