# MEMCG-005D External-Migration First-Touch Result v1

> **Status:** PASS / REJECT_EXTERNAL_PATH
> **Run:** `36553495930`
> **Relaunch commit:** `098607e7b8f76377841a718799d896f50a0bef12`
> **Aggregate artifact id:** `11026260063`
> **Aggregate digest:** `sha256:caa5d2962665855627b8041b2ab4649dfcc01b14a5427a4ee53f419a7c4d0437`

## Primary decision

`REJECT_EXTERNAL_PATH`

The controller-driven external migration path did not restore a reliable fresh-Q64 first touch.

## Aggregate

### SELF_ATOMIC

- Q64: **68 / 92**
- failures: **24 / 92**
- success rate: **0.7391304348**
- zero-delta failures: **24**
- other deltas: **0**

### EXTERNAL_ATOMIC

- Q64: **63 / 92**
- failures: **29 / 92**
- success rate: **0.6847826087**
- zero-delta failures: **29**
- other deltas: **0**
- perfect blocks: **0 / 4**
- CPU mismatches: **0**
- 95% Clopper-Pearson success interval:
  **[0.5795743616, 0.7777114356]**

External migration was not better overall.

## Blockwise external failure counts

- block0: 12 / 23
- block1: 5 / 23
- block2: 6 / 23
- block3: 6 / 23

SELF failures:

- block0: 5 / 23
- block1: 9 / 23
- block2: 5 / 23
- block3: 5 / 23

EXTERNAL improved only block1.

The preregistered paired one-sided sign test returned:

`p = 0.9375`

for external improvement.

## Migration / touch decomposition

For EXTERNAL_ATOMIC:

`migration_delta_pages = 0`

for **92 / 92** probes.

The measured touch then produced only:

- `+64`, or
- `0`.

Therefore controller-driven migration did not itself create an observable net `memory.current` jump.

Nevertheless 29/92 later first touches were zero-delta.

This rejects the simple explanation:

**the worker's own migration syscall is the dominant cause of first-touch zero-delta events.**

A zero migration delta does not prove hidden memcg stock state was unchanged, because offsetting charge/uncharge activity can be net-zero.

## Secondary paired table

Matched by block and identity:

- both pass: 45
- SELF only pass: 23
- EXTERNAL only pass: 18
- both fail: 6

No clear external-path advantage appears.

## Post-hoc baseline diagnostic

This diagnostic was not preregistered and does not change the primary decision.

Using the pre-touch `memory.current` value:

### SELF_ATOMIC

For:

`pre_current <= 110 pages`

Q64 success was:

`46 / 46`

For:

`pre_current > 110 pages`

Q64 success was:

`22 / 46`

### EXTERNAL_ATOMIC

For:

`pre_current <= 110 pages`

Q64 success was:

`38 / 39`

For:

`pre_current > 110 pages`

Q64 success was:

`25 / 53`

The independent one-sided Fisher associations are strong post-hoc signals, but the threshold was selected after seeing MEMCG-005D and therefore requires prospective validation.

## Accepted conclusion

MEMCG-005D rejects EXTERNAL_ATOMIC as a reliable insertion primitive.

It also shows that:
- post-migration status I/O is not the dominant problem;
- worker self-migration is not the dominant problem;
- the first-touch observable remains quantized strictly at 0 or +64;
- pre-touch cgroup charge level is a strong candidate predictor of which state is present.

## Next experiment

MEMCG-005E prospectively validates the frozen baseline threshold:

`LOW iff pre_current_pages <= 110`

and compares first touch on:
- startup CPU P;
- remote stock CPU S.

Do not return to K7 capacity inference until this predictor is independently validated.

## Authority boundary

Hosted Linux accounting research only.
No local-PC execution.
No memory-control policy.
