# MEMCG-005 Calibrated K7 Result v1

> **Status:** PASS / INCONCLUSIVE / NORMALIZATION-STATE INTERFERENCE EXPOSED
> **Run:** `36545631176`
> **Launch commit:** `b8c1cfbf4e54fef37a314fbe629fceef4734ff0b`
> **Aggregate artifact id:** `11021643891`
> **Aggregate digest:** `sha256:91ea4a9b6e2b256bd7031f0c99a1cf0fa649bc1a53d6a9724a049a9dde03350c`

## Primary decision

`INCONCLUSIVE`

Support blocks:

`0 / 4`

Complete-valid blocks:

`0 / 4`

Systematic invalid-state pattern:

`true`

The experiment successfully executed, but the intended calibrated-EMPTY precondition was not maintained reliably across the multi-worker preparation phase.

## Replica validity

20 independent replicas were attempted:

`4 blocks x m={0,5,6,7,8}`

Valid one-shot target-state replicas:

`11 / 20`

Invalid-by-m:

- m=0: 1 / 4
- m=5: 0 / 4
- m=6: 3 / 4
- m=7: 3 / 4
- m=8: 2 / 4

Invalid reasons were always a measured insertion that failed to produce the required fresh Q64 charge.

## Observed block states

### block 0
- m0: PRESENT
- m5: ABSENT
- m6: PRESENT
- m7: INVALID — c3 INSERT_NOT_Q64
- m8: ABSENT

### block 1
- m0: PRESENT
- m5: ABSENT
- m6: INVALID — w2 INSERT_NOT_Q64
- m7: ABSENT
- m8: INVALID — c7 INSERT_NOT_Q64

### block 2
- m0: INVALID — w4 INSERT_NOT_Q64
- m5: ABSENT
- m6: INVALID — w5 INSERT_NOT_Q64
- m7: INVALID — w5 INSERT_NOT_Q64
- m8: INVALID — c6 INSERT_NOT_Q64

### block 3
- m0: PRESENT
- m5: PRESENT
- m6: INVALID — c6 INSERT_NOT_Q64
- m7: INVALID — t0 INSERT_NOT_Q64
- m8: PRESENT

No block provided the complete preregistered source signature:

`PRESENT, PRESENT, PRESENT, ABSENT, ABSENT`

for:

`m=0,5,6,7,8`.

## Model competition on nominally valid replicas

There were 11 nominally valid target-state observations.

Classification errors:

- K in {1,2,3,4,5}: 3 errors
- K=6: 5 errors
- K=7: 4 errors
- K=8: 5 errors
- K=9: 5 errors

Thus the analyzer reports:

`best K = {1,2,3,4,5}`

for error, log-loss, and MDL.

This is **not accepted as a mechanistic capacity estimate**, because the calibration-precondition diagnostics below show that no replica had a fully clean used-identity normalization sequence.

## Critical normalization diagnostic

MEMCG-005 normalized an identity by:

1. observe a fresh +64 charge;
2. issue 63 later page touches as one `TOUCH_N 63` command;
3. assume the stock is now empty.

The aggregate evidence shows this assumption failed frequently.

For every one of the 9 insertion failures:

- the failing identity's prior `consume63_delta_pages` was exactly +64;
- its later measured insertion delta was exactly 0.

Thus:

`9 / 9 INSERT_NOT_Q64 failures`

were preceded by:

`consume63_delta_pages = +64`

for that same identity.

This is direct evidence that the intended EMPTY state had not been established for those identities.

## Stronger post-hoc diagnostic

Every one of the 20 replicas used at least one identity whose normalization window showed:

`consume63_delta_pages = +64`.

Therefore **no replica had a globally clean preparation sequence under the intended model**.

Some identities with this anomaly later did produce a fresh +64 insertion, implying that intervening cache activity changed their state again before insertion.

That observation is itself evidence that pre-normalizing many identities on the measured stock CPU does not preserve a stable known state until later insertion.

This diagnostic is post-hoc and is not used to rewrite the preregistered primary decision.

## Source-level explanation candidate

The inspected Linux implementation allows several routes by which a previously calibrated stock state can change:

- `consume_stock()` is guarded by `local_trylock(&memcg_stock.lock)`;
- a failed stock consumption path can fall back into a fresh batch charge;
- `refill_stock()` modifies the current CPU's shared seven-slot cache;
- when no empty slot exists, `drain_idx` replacement can drain another memcg's stock;
- kernel-memory/socket uncharges can also refill memcg stock.

In a 16-worker same-CPU preparation phase, the experimental act of preparing many identities therefore interacts with the exact shared cache being studied.

## Accepted conclusion

MEMCG-005 does **not** reject or support K=7.

It demonstrates that:

**preparing many memcg identities on the stock-test CPU before the measured insertion sequence is itself a state-changing intervention.**

The successful single-worker calibration primitive from MEMCG-004 does not automatically compose into a 16-worker same-CPU calibration protocol.

This is a compositionality failure, not a failure of Q64.

## Next repair principle

Do not prepare future identities on the measured stock CPU.

Use three CPU roles:

- C: controller
- P: preparation / startup CPU
- S: stock-test CPU

Workers should start on P and remain untouched on S until their measured insertion.

The first measured touch after migration to S must itself be the insertion verification.

To eliminate unknown initial S-cache occupancy, use more than one full cache cycle of distinct verified wash insertions before the target.

## Authority boundary

Hosted Linux accounting research only.
No local-PC execution.
No memory-control policy.
