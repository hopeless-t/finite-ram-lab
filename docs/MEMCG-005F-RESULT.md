# MEMCG-005F Remote-Low Admission Gate Result v1

> **Status:** PASS / SUPPORT_REMOTE_LOW_GATE
> **Run:** `36558350433`
> **Launch commit:** `15c0ac94f0bd5707cec327eaa6f44a6fdb2c8520`
> **Aggregate artifact id:** `11028742104`
> **Aggregate digest:** `sha256:42d4eccb8b6030132b56e93f7c85dbcb13d17796657c2361d583ccaee136ced8`

## Primary decision

`SUPPORT_REMOTE_LOW_GATE`

Frozen confirmatory predicate:

`REMOTE_LOW := startup CPU P, measured CPU S != P, pre_current_pages <= 110`

The rule was fixed before launch and was not retuned.

## Primary result

### LOW

- valid n: **123**
- Q64 successes: **121**
- failures: **2**
- success rate: **98.37398374%**
- zero-delta failures: **2**
- other-delta failures: **0**

### HIGH

- valid n: **133**
- Q64 successes: **65**
- failures: **68**
- success rate: **48.87218045%**
- zero-delta failures: **68**
- other-delta failures: **0**

Admission yield:

`123 / 256 = 48.046875%`

Primary one-sided Fisher exact test LOW > HIGH:

- odds ratio: **63.2923076923**
- p: **5.9323458707e-22**

CPU mismatches:

`0`

Migration delta:

`0 pages in 256 / 256 probes`

Non-{0,Q64} failure morphology:

`0`

## Blockwise LOW replication

- block0: **31/31 = 100%**
- block1: **31/32 = 96.875%**
- block2: **39/40 = 97.5%**
- block3: **20/20 = 100%**

Every block satisfying the preregistered minimum LOW sample size exceeded the 90% block success threshold.

## Decision-rule audit

SUPPORT required:

- LOW n >=120: **123 PASS**
- LOW success >=97%: **98.374% PASS**
- each block with >=20 LOW has success >=90%: **PASS**
- HIGH success <=60% when HIGH n>=40: **48.872% PASS**
- Fisher p <1e-10: **5.93e-22 PASS**
- CPU mismatches=0: **PASS**
- no non-{0,Q64} failures: **PASS**

Therefore the preregistered decision is unambiguously:

`SUPPORT_REMOTE_LOW_GATE`

## Accepted conclusion

The combination of:

1. starting the worker on P;
2. measuring the first target page on a distinct CPU S;
3. admitting only identities with pre-touch `memory.current <=110 pages`;

predicts a fresh Q64 first-touch event with high reliability in this hosted environment.

The scalar baseline alone is insufficient; CPU locality is part of the gate.

This is now an independently confirmed admission primitive rather than a post-hoc pattern.

## What this does not establish

MEMCG-005F does **not** establish:

- NR_MEMCG_STOCK=7 experimentally;
- slot capacity;
- eviction order;
- a hardware memory law;
- general validity outside the tested hosted Linux environment.

A successor capacity experiment must still verify every admitted insertion directly with Q64.

## Successor principle

A future K-boundary experiment may:

- create candidates on P;
- measure pre-touch baseline before S-side use;
- discard HIGH identities before they touch S;
- migrate only REMOTE_LOW candidates to S;
- require the actual first S-side touch to verify Q64;
- use only verified admitted identities in the capacity sequence.

Hosted research only.
No local-PC execution.
No memory-control policy.
