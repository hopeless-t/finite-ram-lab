# MEMCG-005B Three-CPU Staged K7 Result v1

> **Status:** PASS / INCONCLUSIVE / MIGRATION-RECEIPT INTERFERENCE EXPOSED
> **Run:** `36547649316`
> **Launch commit:** `73baca88f9701c1d819cdb9a11da38d033669aff`
> **Aggregate artifact id:** `11023071670`
> **Aggregate digest:** `sha256:3f7f6998536cc945d0a6a32d267b43b271375454b9cee4b4ebe743976089a474`

## Primary decision

`INCONCLUSIVE`

Support blocks:

`0 / 4`

Complete-valid blocks:

`1 / 4`

Systematic invalid-state pattern:

`true`

## Validity matrix

20 replicas were attempted.

Invalid-by-m:

- m=0: 2 / 4
- m=5: 2 / 4
- m=6: 1 / 4
- m=7: 1 / 4
- m=8: 0 / 4

Six replicas failed because one measured insertion produced:

`delta_pages = 0`

instead of a fresh Q64-like charge.

Invalid identities:

- block0 m0: w13
- block0 m5: w0
- block0 m6: w0
- block0 m7: c4
- block1 m5: w0
- block2 m0: w2

All six had a successful MIGRATE receipt reporting:

`cpu=3 touched=0`

before the zero-delta measured touch.

## Valid target-state observations

Among valid replicas:

### m=0
- PRESENT: 2 / 2

### m=5
- PRESENT: 1 / 2
- ABSENT: 1 / 2

### m=6
- ABSENT: 3 / 3

### m=7
- ABSENT: 3 / 3

### m=8
- ABSENT: 4 / 4

Thus the valid subset does not show the preregistered K7 signature.

The only complete-valid block was block3:

`PRESENT, PRESENT, ABSENT, ABSENT, ABSENT`

for:

`m=0,5,6,7,8`

which is compatible with a boundary at K=6, not K=7.

However this cannot be promoted to a capacity estimate because the experiment still had systematic insertion-validity failure.

## Model competition

Across 14 valid observations:

- K={1,2,3,4,5,6}: 1 classification error
- K=7: 4 errors
- K=8: 7 errors
- K=9: 11 errors

The nominal best equivalence class is:

`K in {1,2,3,4,5,6}`

This is not accepted as a mechanistic estimate.

## Critical control-path flaw

MEMCG-005B intended:

**no participant demand on S before its measured insertion touch.**

The worker implementation performed:

1. `sched_setaffinity(...S...)`
2. wait until `sched_getcpu()==S`
3. `fprintf(status, "MIGRATE ...")`
4. later receive `TOUCH_ONE`

Therefore the MIGRATE receipt itself executes after the worker has arrived on S.

The status-I/O path may perform user/kernel work charged to the memcg on S before the nominal measured touch.

This violates the experiment's strongest intended invariant:

**first S-side demand = measured TOUCH_ONE.**

The six zero-delta insertion failures are source-consistent with the possibility that stock was established/consumed by post-migration control-path activity before TOUCH_ONE.

This explanation is a mechanism hypothesis, not yet causal proof.

## Accepted conclusion

MEMCG-005B does not support or reject K=7.

It does show:

- three-CPU staging improved validity relative to same-CPU pre-normalization;
- all valid m=6 observations were already ABSENT;
- but the migration receipt path still permits pre-measurement S-side activity;
- therefore the K boundary remains confounded.

The next experiment must test the control-path invariant directly.

## Next experiment

MEMCG-005C should compare:

### TWO_STEP
`MIGRATE S -> receipt -> TOUCH_ONE`

versus:

### ATOMIC
`MIGRATE_TOUCH S`

where ATOMIC performs:

1. `sched_setaffinity(...S...)`
2. confirm current CPU without I/O;
3. immediately touch one pre-mapped measured page;
4. only then emit any receipt.

Use many fresh identities and score the rate of Q64 first-touch verification.

Do not run another K7 capacity experiment until the atomic insertion path is validated.

## Authority boundary

Hosted Linux accounting research only.
No local-PC execution.
No memory-control policy.
