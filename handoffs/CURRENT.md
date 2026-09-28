# CURRENT

> **Latest bounce:** B295
> **Stage:** MEMCG-002 IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Accepted chain

MEMCG-001:
`SUPPORT_H64`

MATH-001:
`MODEL64_WINS`

MATH-001 details:
- Q64 reset-aware SSE = 0
- Q64 minimum MDL = 30 bits
- Q64 leave-one-block-out F1 = 1.0 in 4/4 folds

## MEMCG-002

Exact implementation:

`19776a4c50412d5b929f8b1130f83b22e2345f04`

Study:
- 4 blocks
- 4 arms
- 16 trials
- startup pinned on CPU A
- deliberate A->B migration after step128
- optional B->A return after step192
- same fresh cgroup and process

Primary causal test:
does CPU migration reset the Q64 phase in the source-predicted direction while return to A restores old A state?

Ordinary CI:

`36454940719`

Single B295 read:

`queued`

Do not poll again in this bounce.

## Next fresh-bounce action

Read CI `36454940719` exactly once.

- success -> explicit MEMCG-002 hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Local follow-up

Only after hosted causal evidence:
prepare an exact-worker Lubuntu replication through MVCA -> LDC under its own bound execution scope.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
