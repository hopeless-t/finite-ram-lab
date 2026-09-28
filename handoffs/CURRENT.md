# CURRENT

> **Latest bounce:** B303
> **Stage:** MEMCG-003 IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Accepted chain

MEMCG-001: `SUPPORT_H64`
MATH-001: `MODEL64_WINS`
MEMCG-002: naive durable per-CPU model rejected; source-corrected seven-slot shared-cache hypothesis retained.

## MEMCG-003

Implementation:
`b64f32ad3b38d4a6ca8bdfda36e4c12fe62d5569`

Ordinary CI:
`36459629772`

Single B303 read:
`in_progress`

Do not poll again in this bounce.

No launch marker exists.

Experiment:
- fill seven persistent wash memcgs on one CPU;
- insert target;
- add distinct challengers one by one;
- probe target after each insertion;
- infer first eviction threshold E.

Controls:
- same-memcg repeated activity
- six-only challengers
- no-churn

Candidate K:
`1..10`

Source prediction:
`K=7`

## Next fresh-bounce action

Read CI `36459629772` exactly once.

- success -> explicit MEMCG-003 hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
