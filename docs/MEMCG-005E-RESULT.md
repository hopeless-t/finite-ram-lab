# MEMCG-005E Baseline-Stratified First-Touch Result v1

> **Status:** PASS / REJECT_BASELINE_GATE / REMOTE_LOW SECONDARY SIGNAL
> **Run:** `36556517823`
> **Launch commit:** `421adf66d76df37d2a00a743f775ba26ef2bb16e`
> **Aggregate artifact id:** `11027928106`
> **Aggregate digest:** `sha256:98c0e50cd4c4cbb6b0bb277c13925e62a55e1f3c1b2fa14ced6508df31f7313d`

## Primary decision

`REJECT_BASELINE_GATE`

The frozen baseline threshold alone did not define a reusable insertion gate across both CPU-locality arms.

Frozen threshold:

`LOW iff pre_current_pages <= 110`

No threshold tuning was performed after launch.

## Pooled result

### LOW

- valid n: **160**
- Q64 successes: **89**
- failures: **71**
- success rate: **55.625%**
- zero-delta failures: **71**
- other failure magnitudes: **0**

### HIGH

- valid n: **96**
- Q64 successes: **9**
- failures: **87**
- success rate: **9.375%**
- zero-delta failures: **87**
- other failure magnitudes: **0**

LOW exceeded HIGH by:

**46.25 percentage points**

Primary one-sided Fisher exact test:

- odds ratio: **12.1173708920**
- p: **9.6353998748e-15**

The association is strong, but the preregistered gate required LOW success >=95% overall and >=90% in both CPU arms. That condition failed.

## CPU-locality split

### LOCAL_P

All 128 probes were zero-delta.

LOW:
- n=70
- Q64=0/70

HIGH:
- n=58
- Q64=0/58

Overall:

`0 / 128 Q64`

### REMOTE_S

LOW:
- n=90
- Q64=89/90
- success rate: **98.8889%**

HIGH:
- n=38
- Q64=9/38
- success rate: **23.6842%**

Overall:

`98 / 128 Q64`

CPU mismatch count:

`0`

All affinity/reassert migration deltas were:

`0 pages`

## Blockwise REMOTE_S LOW replication

- block0: 16/16
- block1: 26/26
- block2: 23/23
- block3: 24/25

The single REMOTE_S LOW failure was:

- block3
- identity7
- pre_current=99 pages
- migration_delta=0
- touch_delta=0
- affinity_to_go_us=225.934

## Accepted interpretation

The primary hypothesis **baseline alone is a reusable gate** is rejected.

The preregistered secondary locality analysis reveals a stronger composite condition:

**REMOTE_S AND pre_current_pages <= 110**

which produced 89/90 fresh Q64 first touches.

By contrast, LOCAL_P produced no fresh Q64 event at all.

This is source-consistent with startup activity on P leaving usable stock for the worker's memcg, so the later measured touch consumes existing stock rather than charging a fresh batch.

That mechanism interpretation is plausible but is not yet a causal proof.

## Measurement lesson

The hidden state is strongly CPU-local.

A scalar cgroup-level `memory.current` threshold is informative but insufficient without CPU locality.

The observed first-touch morphology remains binary:

- +64 pages
- 0 pages

with no intermediate failure magnitudes.

## Next experiment

MEMCG-005F promotes the composite condition to the primary prospective hypothesis:

`REMOTE_LOW := target CPU != startup CPU AND pre_current_pages <= 110`

No threshold or CPU rule may change after launch.

Only after independent SUPPORT_REMOTE_LOW_GATE may this gate be used to admit identities into a successor slot-capacity experiment.

## Authority boundary

Hosted Linux accounting research only.
No local-PC execution.
No memory-control policy.
