# CURRENT

> **Latest bounce:** B321
> **Stage:** MEMCG-005 IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## MEMCG-004 accepted primitive

Canonical commit:
`acdcb6e28baa448cd5f38d7ef960b6bbf321ac80`

Decision:
`SUPPORT_CALIBRATED_STOCK`

Exact calibrated phase:
`R=[64,64,64,64]`

## MEMCG-005

Design:
`docs/MEMCG-005-CALIBRATED-K7-v1.md`

Implementation:
`81118055839291dc3f939c0b7ff01ca7080cf343`

Per replica:
- prestart W0..W6 + T + C1..C8;
- normalize every identity to EMPTY using observed +64 then exactly 63 consumptions;
- require each measured insertion touch to be +64;
- insert 7 washes;
- insert target;
- insert m challengers;
- one-shot target state probe;
- terminate.

Independent m:
`{0,5,6,7,8}`

Source K7 signature:
- m0/5/6 PRESENT
- m7/8 ABSENT

Candidate K:
`1..9`

Sparse observational equivalence classes are reported explicitly.

Ordinary CI:
`36544481855`

Single B321 read:
`queued`

Do not poll again in this bounce.

No launch marker exists.

## MATH-002

Still infrastructure-failed / no scientific result.
Secondary only.

## Next fresh-bounce action

Read CI `36544481855` exactly once.

- success -> explicit MEMCG-005 hosted launch in a separate bounce;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
