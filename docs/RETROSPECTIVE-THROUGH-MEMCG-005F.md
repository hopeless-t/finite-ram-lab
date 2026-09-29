# Finite RAM Lab Retrospective — Through MEMCG-005F

> **Checkpoint:** B356
> **Theme:** from a suspicious ~256 KiB pattern to a source-grounded, experimentally calibrated memcg accounting primitive.

## 1. Where the project started

The project began with finite-RAM pressure behavior and a suspicious near-256 KiB structure.

The early "777" interpretation did not survive falsification.

What survived was more interesting:

- a reproducible pressure-knee phenomenon;
- a 64-page / 256 KiB accounting quantum;
- a CPU-local hidden memcg stock state;
- and, eventually, a practical admission predicate for obtaining a fresh Q64 first touch.

The project therefore moved from numerical coincidence hunting to mechanism identification and measurement calibration.

## 2. Finite-RAM pressure results that survived

### Sliding DONTNEED materially reduces retained cold-file cache

STRATA-002 found a median post-scan resident reduction of roughly **52.13%** and recovered about **83.46 MiB** of headroom at MemoryHigh=160 MiB.

### The H160 knee is real

STRATA-004 established:

`80 < K <= 88 MiB`

for the H160 / hot64 / cold96 configuration.

### The more stable invariant is effective live set

STRATA-006 varied hot memory and found:

`144 < K + hot <= 152 MiB`

across hot56/64/72.

This was stronger than treating K alone as a universal constant.

### The effect crossed image/version boundaries

STRATA-007 reproduced the knee/transformed interval on Ubuntu 26.

### Streaming beyond MemoryMax can remain bounded

STRATA-009 used cold384 with MemoryMax320 and passed 20/20 under DONTNEED, showing that a streaming working set larger than MemoryMax need not imply OOM when cold pages are actively discarded.

## 3. The measurement system itself was part of the phenomenon

REC-003 showed that the historical `_file_residency` observer introduced target-size-dependent cgroup footprint, including an approximately 256 KiB effect at larger targets.

That invalidated a pure-workload interpretation of some earlier floor measurements.

REC-004 then measured clean pre-observer floors:

- 12.6875 MiB
- 12.8046875 MiB
- 12.935546875 MiB

with total span:

`0.248046875 MiB`

and clustering near quarter-MiB spacing.

This was the first major lesson of the later memcg work:

**the observer and control path can alter the hidden state being inferred.**

## 4. The 256 KiB structure was tied to Linux memcg source

Pinned Linux source showed:

`MEMCG_CHARGE_BATCH = 64`

with 4 KiB pages:

`64 pages = 256 KiB`

The same source exposed:

- per-CPU memcg stock;
- seven stock slots;
- stock consume/refill/drain behavior;
- replacement via `drain_idx`;
- other refill paths such as object-cgroup and socket uncharge;
- global/pressure-driven drains.

This changed the 256 KiB observation from an unexplained numeric pattern into a source-grounded accounting hypothesis.

## 5. Q64 was experimentally established

MEMCG-001 produced repeated exact +64-page events and supported the 64-page accounting model.

MATH-001 then compared reset-aware quantization models:

- Q64 achieved zero SSE;
- MDL strongly favored Q64;
- leave-one-block-out selected Q64 with held-out F1=1.0.

The accepted hosted model became:

**resettable Q64 accounting staircase with hidden phase/state.**

It was explicitly not treated as a hardware law.

## 6. Naive stock models were falsified instead of protected

MEMCG-002 rejected the simple durable one-stock-per-CPU model.

MEMCG-003 attempted a seven-slot eviction experiment but exposed a destructive observer: the target probe itself consumed target stock.

MEMCG-003B repaired the observer but showed that passive `memory.current` drop was not a reliable proxy for stock eviction.

These failures were productive: each removed one invalid inference path.

## 7. MEMCG-004 established a calibrated stock phase

MEMCG-004 was a major positive result.

Across four blocks:

- first fresh Q64 was calibrated;
- the next 63 touches produced no fresh Q64;
- touch64 produced +64 in every block.

Validation:

`R = [64,64,64,64]`

CONTROL_NO_PRIME instead produced arbitrary early recharge positions.

This experimentally established a reproducible calibrated stock phase:

fresh one-page miss -> +64 batch -> 63 residual stock pages -> 63 stock-consuming touches -> next touch recharges +64.

This result survived while stronger seven-slot claims remained unproven.

## 8. The seven-slot experiment became a study of compositional interference

MEMCG-005 tried to compose many calibrated identities on one stock CPU.

It failed because preparation itself perturbed the shared stock cache.

MEMCG-005B separated startup and stock CPUs and improved validity, but still produced systematic zero-delta insertions.

MEMCG-005C tested whether post-migration receipt I/O caused those failures.

It did not:

- ATOMIC: 69/92 Q64
- TWO_STEP: 77/92 Q64

The proposed repair made performance worse.

MEMCG-005D removed worker self-migration from one arm.

It also failed as a universal repair:

- SELF: 68/92 Q64
- EXTERNAL: 63/92 Q64
- external migration delta: 0 in 92/92.

Thus neither receipt I/O nor self-migration was the dominant explanation.

## 9. The hidden state turned out to be strongly CPU-local and baseline-dependent

MEMCG-005D revealed a post-hoc baseline signal.

MEMCG-005E prospectively froze:

`LOW iff pre_current_pages <=110`

but the pooled baseline-only gate was rejected.

The crucial registered secondary split was:

### LOCAL_P
`0/128 Q64`

### REMOTE_S LOW
`89/90 Q64`

### REMOTE_S HIGH
`9/38 Q64`

This showed that baseline alone was not enough.

The useful structure was composite:

**remote CPU + low pre-touch baseline.**

## 10. MEMCG-005F independently confirmed the composite gate

MEMCG-005F promoted that composite rule to the primary confirmatory hypothesis:

`REMOTE_LOW := startup P, measured S!=P, pre_current_pages<=110`

Result:

- LOW: **121/123 = 98.374% Q64**
- HIGH: **65/133 = 48.872% Q64**
- odds ratio: **63.29**
- Fisher one-sided p: **5.93e-22**
- CPU mismatches: **0**
- migration delta: **0 in 256/256**
- non-{0,+64} failures: **0**

LOW replication by block:

`31/31, 31/32, 39/40, 20/20`

Decision:

`SUPPORT_REMOTE_LOW_GATE`

This is the strongest operational primitive produced by the memcg branch so far.

## 11. What the project has actually achieved

The project did **not** prove a seven-slot runtime boundary yet.

It achieved something more foundational first:

1. separated real finite-RAM pressure behavior from observer artifacts;
2. identified the 64-page source mechanism behind the 256 KiB quantum;
3. established Q64 experimentally and statistically;
4. calibrated a reproducible 64-touch stock phase;
5. falsified multiple attractive but incorrect measurement assumptions;
6. demonstrated that memcg stock behavior is strongly CPU-local;
7. produced and independently confirmed a practical admission gate for fresh remote Q64 insertions.

The current experimentally supported chain is:

`REMOTE_LOW candidate`
→ migrate P to S
→ first S-side measured page touch
→ **98.37% fresh Q64 in confirmatory data**

with every actual insertion still requiring direct Q64 verification.

## 12. What remains open

The central unresolved mechanism question is now narrower:

**Using only admitted-and-verified REMOTE_LOW identities, does runtime eviction exhibit the source-predicted seven-slot rotating boundary?**

That is now testable with a much cleaner primitive than MEMCG-003/005 had.

Other open questions include:

- why pre-touch cgroup baseline is such a strong proxy for remote-stock freshness;
- why startup CPU P yielded 0/128 fresh Q64 in MEMCG-005E;
- whether the REMOTE_LOW gate generalizes across kernels/runner images/CPU counts;
- how background kmem/socket refund paths contribute to the remaining ~1.6% LOW failures.

## 13. Methodological result

The project repeatedly benefited from refusing to promote a convenient story:

- 777 was allowed to fail;
- observer contamination was admitted;
- K7 was not inferred from censored or invalid subsets;
- receipt-I/O and self-migration hypotheses were directly tested and rejected;
- post-hoc <=110 was not accepted until a separate confirmatory experiment;
- primary and secondary analyses remained distinct.

The resulting knowledge is narrower than the early story, but much stronger.

## Current checkpoint

MEMCG-005F:

`SUPPORT_REMOTE_LOW_GATE`

This closes the current measurement-calibration chapter.

The next scientific chapter can return to capacity/eviction testing using the validated admission primitive.
