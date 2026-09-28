# CURRENT

> **Latest bounce:** B297
> **Stage:** MEMCG-002 ANALYZER REPAIR + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Accepted chain

MEMCG-001:
`SUPPORT_H64`

MATH-001:
`MODEL64_WINS`

## MEMCG-002

Scientific design unchanged:
- FIXED_TOUCH
- MIGRATE_TOUCH A->B after step128
- ROUNDTRIP_TOUCH A->B after128, B->A after192
- ROUNDTRIP_CONTROL

Repair commit:
`3e563db223c80938a09a8a1567c8b9fe4e5836d4`

Repair:
- MIGRATE_TOUCH B-side now spans all steps after128 through256.
- ROUNDTRIP B-side remains129..192.

Repair CI:
`36455336164`

Single B297 read:
`in_progress`

Do not poll again in this bounce.

No launch marker exists.

## Next fresh-bounce action

Read `36455336164` exactly once.

- success -> explicit MEMCG-002 hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
