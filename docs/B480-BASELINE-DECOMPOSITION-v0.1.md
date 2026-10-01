# B480 — Baseline Normalization Decomposition v0.1

Status: **MEASUREMENT-DECOMPOSITION EXPERIMENT**.

## 1. Why this experiment is necessary

B479 replicated the seed effect across eight hosted-runner blocks:

- q2 normalized seed delta median ~= -146 KiB;
- q4 normalized seed delta median ~= -125 KiB.

However the primary endpoint is:

```text
normalized peak growth
=
absolute work VmHWM
-
pre-work baseline VmHWM
```

The baseline is recorded after seed-dependent input generation.

Therefore a seed effect in the normalized endpoint does not automatically imply a
seed effect in the absolute work-phase memory peak.

## 2. Three quantities

B480 records all three quantities explicitly:

1. baseline VmHWM;
2. absolute work VmHWM;
3. normalized peak growth.

For every child:

```text
normalized
=
max(0, absolute_work_peak - baseline)
```

The identity is fail-closed.

## 3. Runner-block design

Eight independent GitHub-hosted job blocks.

Per block:

- q2 seed474 x2
- q2 seed476 x2
- q4 seed474 x2
- q4 seed476 x2

The condition order and reverse-order pairing mirror B479.

Total child observations:

`64`.

## 4. Block-level decomposition

For each q and each runner block:

```text
delta_baseline = baseline(476) - baseline(474)

delta_work =
absolute_work_peak(476) - absolute_work_peak(474)

delta_normalized =
normalized(476) - normalized(474)
```

With two replicates per condition, the median is the arithmetic midpoint, so the
difference identity remains directly inspectable at block-summary level.

## 5. Confirmatory tests

Six familywise tests:

- q2 normalized seed effect, directional negative;
- q2 baseline seed effect, two-sided;
- q2 absolute-work seed effect, two-sided;
- q4 normalized seed effect, directional negative;
- q4 baseline seed effect, two-sided;
- q4 absolute-work seed effect, two-sided.

Family alpha:

`0.05`

Bonferroni threshold:

`0.05/6 ~= 0.008333`

With eight nonzero blocks, a two-sided sign test requires all eight blocks in the
same direction to cross that threshold.

## 6. Interpretation classes

Per q:

### BASELINE_NORMALIZATION_EFFECT

Baseline differs significantly, absolute work peak does not.

The apparent seed effect is primarily a property of the subtraction baseline.

### ABSOLUTE_WORK_PEAK_EFFECT

Absolute work peak differs significantly, baseline does not.

The seed-sensitive effect reaches the actual process high-water mark.

### MIXED_ABSOLUTE_AND_BASELINE_EFFECT

Both components move.

### NORMALIZED_EFFECT_COMPONENT_UNRESOLVED

The normalized difference replicates but the decomposition components do not
individually resolve at the frozen threshold.

## 7. Why this matters

If the q seed effect is baseline-only, a workload-conditioned memory governor
would be learning the measurement protocol rather than the resource requirement.

If the absolute work peak moves, workload identity belongs in the physical
resource model.

## 8. Claim ceiling

**GITHUB_HOSTED_BLOCK_NORMALIZATION_DECOMPOSITION**

## 9. Next

The B480 result decides whether the next governor axis is:

- workload-conditioned physical peak;
- revised baseline/measurement semantics;
- or a mixed hierarchical model.
