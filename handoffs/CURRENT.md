# CURRENT

> **Latest bounce:** B338
> **Stage:** MEMCG-005C REJECTED / MEMCG-005D EXTERNAL-MIGRATION DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## MEMCG-005C canonical result

Run:
`36551226475`

Decision:
`REJECT_ATOMIC_PATH`

ATOMIC:
- 69/92 Q64
- 23/92 zero-delta failures
- success rate 0.75
- 0/4 perfect blocks

TWO_STEP:
- 77/92 Q64
- 15/92 zero-delta failures
- success rate 0.8369565

ATOMIC was worse in 4/4 blocks despite arm-order reversal across block parity.

Therefore post-migration receipt I/O is not supported as the dominant failure mechanism.

Canonical result:
`docs/MEMCG-005C-RESULT.md`

## MEMCG-005D

Frozen design:
`docs/MEMCG-005D-EXTERNAL-MIGRATION-FIRST-TOUCH-v1.md`

A/B:
- SELF_ATOMIC = worker self-migrates then immediate touch;
- EXTERNAL_ATOMIC = controller externally migrates spinning worker, then shared-memory GO causes immediate touch.

No worker control/status I/O is allowed between shared READY and measured touch.

23 identities per arm per block, 4 blocks.

## Next fresh-bounce action

Implement MEMCG-005D only:
- shared-latch worker;
- external PID affinity change;
- SELF vs EXTERNAL arms;
- exact delta/CPU receipts;
- analyzer/tests/workflow.

Do not launch during implementation.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
