# CURRENT

> **Latest bounce:** B319
> **Stage:** MEMCG-005 CALIBRATED SEVEN-SLOT DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## MEMCG-004 accepted result

Canonical commit:
`acdcb6e28baa448cd5f38d7ef960b6bbf321ac80`

Decision:
`SUPPORT_CALIBRATED_STOCK`

Exact calibrated phase:
`R=[64,64,64,64]`

This supplies a validated state primitive.

## MEMCG-005 frozen design

`docs/MEMCG-005-CALIBRATED-K7-v1.md`

Key improvement:
do not infer a stock slot from worker existence.

All worker identities are prestarted first.

Every worker is normalized to EMPTY:
1. find fresh +64;
2. consume exactly 63 pages;
3. stop before next miss.

Every measured insertion is then required to produce a fresh +64 charge.

Independent one-shot replicas test:
`m={0,5,6,7,8}`

Primary K7 signature:
- 0 -> PRESENT
- 5 -> PRESENT
- 6 -> PRESENT
- 7 -> ABSENT
- 8 -> ABSENT

4 blocks × 5 replicas.

Target is probed exactly once per replica.

## MATH-002

pmndrs/math sidecar remains infrastructure-failed with no scientific result.
It is secondary and does not block MEMCG-005.

## Next fresh-bounce action

Implement MEMCG-005 only:
- extend interactive worker with bounded multi-touch command if needed;
- prestart/normalize orchestration;
- verified insertion receipts;
- one-shot target probe;
- sparse-boundary model analyzer with equivalence-class reporting;
- synthetic tests;
- hosted workflow.

Do not launch during implementation.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
