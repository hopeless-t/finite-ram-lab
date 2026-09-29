# CURRENT

> **Latest bounce:** B326
> **Stage:** MEMCG-005B THREE-CPU STAGED DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## MEMCG-005 accepted result

Canonical commit:
`95191357ac80b9157c2f9f05df86672abb661983`

Decision:
`INCONCLUSIVE`

Reason:
many-worker same-CPU pre-normalization perturbed the shared stock state.

## MEMCG-005B

Frozen design:
`docs/MEMCG-005B-THREE-CPU-STAGED-K7-v1.md`

CPU roles:
- C controller
- P prep/startup
- S stock-test

Workers start zero-touch on P.

Measured insertion:
- migrate P -> S;
- first S touch must be +64-like.

No future identity may touch S before its insertion.

Robust prefill:
- 14 distinct verified wash insertions before target.

Reason:
after at most 7 inserts the cache is full; seven more distinct replacements sweep all seven slots, washing out unknown initial occupancy/drain_idx under the source model.

Independent m:
`{0,5,6,7,8}`

Source K7 signature:
- 0/5/6 PRESENT
- 7/8 ABSENT

## Next fresh-bounce action

Implement MEMCG-005B:
- zero-touch worker with MIGRATE command;
- three-CPU runner;
- 14-wash staged insertion;
- one-shot target probe;
- analyzer/tests/workflow.

Do not launch during implementation.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
