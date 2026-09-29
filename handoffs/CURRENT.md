# CURRENT

> **Latest bounce:** B323
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

Implementation CI:
`36544481855 = success`

Launch:
`b8c1cfbf4e54fef37a314fbe629fceef4734ff0b`

Scientific run:
`36545631176`

Single B323 read:
`queued`

Do not poll again in this bounce.

Design:
- prestart 16 worker identities;
- normalize each to EMPTY via observed +64 then 63 consumptions;
- require +64 verified insertions for washes/target/challengers;
- independent m={0,5,6,7,8};
- one-shot target probe.

Source K7 signature:
- m0/5/6 PRESENT
- m7/8 ABSENT

Candidate K:
`1..9`

Sparse observational equivalence classes are reported explicitly.

## Next fresh-bounce action

Read run `36545631176` exactly once.

- success -> fetch aggregate once, inspect validity matrix and boundary signature, canonicalize;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
