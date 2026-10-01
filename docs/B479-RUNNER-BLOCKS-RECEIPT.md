# B479 — Independent Runner-Block Replication Receipt

Status: **PASS / SEED EFFECT REPLICATED ACROSS RUNNER BLOCKS**

## Frozen execution

- workflow run: 36937300214
- aggregate job: 110620735672
- execution head: 7150fa9bccdf0e81f425ca370bfd650cda3afd25
- runner blocks: 8
- child observations: 64
- aggregate artifact ID: 11198013652
- aggregate artifact ZIP SHA256: 3ad4394fc5a5801c51a2d27dc27205655d1fa19b4bceef6feedeb52af717e8b8
- aggregate JSON SHA256: 0b667783ef34e100b2fa5530d8fbc44d6f51c9cef534290d18c6433d1858be8e

## Environment diversity

The eight hosted jobs included multiple CPU models:

- AMD EPYC 9V74
- AMD EPYC 7763
- AMD EPYC 9V45
- Intel Xeon Platinum 8573C

All reported the same GitHub image version:

`20260927.320.1`

Visible memory was approximately 16.37 GB.

## q2 seed effect

Every runner block had:

`seed476 peak < seed474 peak`

Block-level seed deltas ranged in the negative direction.

Median block seed delta:

`-146,432 B`

Exact directional sign test:

- favorable blocks = 8/8
- p = 0.00390625
- significant at Bonferroni alpha 0.0125

Classification:

**q2 seed effect replicated**

## q4 seed effect

Every runner block also had:

`seed476 peak < seed474 peak`

Median block seed delta:

`-128,000 B`

Exact directional sign test:

- favorable blocks = 8/8
- p = 0.00390625
- significant

Classification:

**q4 seed effect replicated**

## q2 temporal / runner component

Current seed474 median minus historical B474 seed474 median was positive in 7/8
runner blocks.

Median delta:

`+22,528 B`

Directional sign-test p:

`0.03515625`

This does not cross the familywise threshold 0.0125.

Therefore the B478 q2 temporal component is **not independently replicated** at
the frozen familywise level.

Runner-block q2 seed474 medians span:

`98,304 B`

which is larger than the B478 historical-vs-current delta.

## q4 temporal control

Positive in 7/8 blocks, but two-sided sign-test:

`p=0.0703125`

not significant.

## Interpretation

The robust result is the seed effect.

The remaining historical/current difference is not yet strong enough to promote
to a persistent temporal drift claim.

However a measurement-level confound remains:

```text
normalized_peak_growth
=
work VmHWM
-
baseline VmHWM
```

and baseline is frozen after seed-dependent input generation.

A replicated seed effect in the normalized value could therefore arise from:

1. a true difference in absolute work-phase peak;
2. a seed-dependent pre-work baseline HWM;
3. both.

## Next

B480 should decompose, block by block:

- baseline VmHWM;
- absolute work VmHWM;
- normalized peak growth.

If absolute work HWM is invariant while baseline differs, the apparent
workload-conditioned memory effect is a normalization artifact and the governor
must not learn seed as a physical peak feature.
