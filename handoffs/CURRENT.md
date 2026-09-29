# CURRENT

> **Latest bounce:** B313
> **Stage:** MATH-002 RUNNING / MEMCG-004 CALIBRATION DESIGN FROZEN
> **Turn stop reason:** EXTERNAL_WAIT

## MEMCG-003B primary

Canonical commit:
`99c084a95fc39c6c4b3ae2081d74117f4355debc`

Decision:
`REJECT_K7_SLOT_MODEL_B`

Accepted interpretation:
- thresholds [null,null,null,null] are right-censored beyond m=8;
- analyzer K9 is not an observed capacity;
- K9 and K10 tie;
- final distinct recharge [0,64,64,64] means stock can be absent without a prior large passive target-current drop.

## MATH-002

Launch:
`15ccd7d06e4786a566c56e3491f07024be6d4424`

Run:
`36529563011`

Single B312 status:
`in_progress`

Do not poll again in this bounce.

## New source-level lesson

A created worker is not a calibrated stock entry.

Source behavior:
- consume-to-zero removes cached pointer;
- refill can modify an existing entry;
- refill beyond batch drains the entry;
- kmem/socket uncharges can refill the same per-CPU memcg stock.

Therefore seven worker identities are not enough to assert seven stable stocked slots.

## MEMCG-004

Frozen design:
`docs/MEMCG-004-CALIBRATED-STOCK-v1.md`

Atomic question:
can a known 63-page stock state be created and verified?

Protocol:
1. one-page touches until an observed +64 charge;
2. stop immediately;
3. passive hold;
4. resume one-page touches;
5. predicted next +64 is validation touch 64.

Only after this calibration passes should seven-slot capacity be retested.

## Next fresh-bounce action

Read MATH-002 run `36529563011` exactly once.

- success -> canonicalize secondary result;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

Then implement MEMCG-004. Do not launch MEMCG-004 during its implementation bounce.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
