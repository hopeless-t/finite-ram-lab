# CURRENT

> **Latest bounce:** B322
> **Stage:** MEMCG-005 EXPLICIT HOSTED LAUNCH
> **Turn stop reason:** RUN_DISCOVERY_PENDING

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

Exact launch commit:
`b8c1cfbf4e54fef37a314fbe629fceef4734ff0b`

Per replica:
- prestart W0..W6 + T + C1..C8;
- normalize each identity to EMPTY using observed +64 then 63 consumptions;
- require measured insertion +64 for washes, target, and challengers;
- one-shot target probe.

Independent m:
`{0,5,6,7,8}`

Source K7 signature:
- m0/5/6 PRESENT
- m7/8 ABSENT

Candidate K:
`1..9`

Sparse observational equivalence classes are reported explicitly.

## Next fresh-bounce action

Discover/read exact-head MEMCG-005 workflow once.

- pending/in_progress -> record run id, EXTERNAL_WAIT;
- success -> fetch aggregate once and canonicalize;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
