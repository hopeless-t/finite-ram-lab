# CURRENT

> **Latest bounce:** B324
> **Stage:** MEMCG-005 HOSTED RUN + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Accepted primitive

MEMCG-004:
`SUPPORT_CALIBRATED_STOCK`

Exact calibrated phase:
`R=[64,64,64,64]`

## MEMCG-005

Implementation:
`81118055839291dc3f939c0b7ff01ca7080cf343`

Launch:
`b8c1cfbf4e54fef37a314fbe629fceef4734ff0b`

Scientific run:
`36545631176`

Single B324 read:
`in_progress`

Do not poll again in this bounce.

Primary source K7 signature:
- m0/5/6 PRESENT
- m7/8 ABSENT

All participating memcgs are calibrated before insertion.

## Next fresh-bounce action

Read run `36545631176` exactly once.

- success -> fetch aggregate once and canonicalize;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
