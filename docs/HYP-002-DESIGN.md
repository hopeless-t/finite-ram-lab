# HYP-002 Design Council — Past Recency vs Future Semantic Need

> **Status:** DESIGN STUDY / MONTE CARLO LAUNCHED

## Question

OBS-003 showed an exploratory asymmetry at 160–162 MiB:

- mapping A was touched before mapping B in the inherited workload;
- mapping A was much more likely to lose residency under strong pressure;
- future HOT semantic identity was balanced independently.

HYP-002 asks:

> Does randomized pre-burst recency/order determine which matched region retains residency, independently of which region will be needed next?

This is an information-gap experiment.

No memory-management hint is introduced.

## Factorial design

Each trial independently declares:

- `recent_identity ∈ {A, B}`;
- `hot_identity ∈ {A, B}`;
- `MemoryHigh ∈ {160, 162} MiB`.

Both regions receive equal touch counts.

Only the final pre-burst ordering changes which region is more recent.

This yields eight cells per runner block:

```text
2 pressure levels
x 2 recent identities
x 2 future HOT identities
= 8 cells
```

## Primary outcome

Immediately before HOT reuse, measure both regions with `mincore(2)`.

Primary block contrast:

```text
mean(recent resident fraction - older resident fraction)
```

averaged across the balanced eight-cell block.

Primary directional hypothesis:

```text
recent fraction > older fraction
```

Final inference will use runner-block sign-flip randomization.

## Key secondary outcome

Because HOT identity is randomized independently of recency identity:

```text
aligned:    HOT == recent
misaligned: HOT == older
```

Compare HOT retouch latency between these conditions at the runner-block level.

This secondary contrast tests the performance consequence of the information mismatch in the same experiment.

## Why another design study

The primary signal looks large in OBS-003, but that observation used a fixed A-before-B order.

HYP-002 reverses/randomizes the order, so some attenuation is plausible.

The design Monte Carlo therefore asks how many independent runner blocks are needed if the true recency effect is only a fraction of the exploratory OBS-003 signal.

## Empirical design input

From the exploratory OBS-003 160/162 MiB data, the pooled runner-block contrast:

```text
recent(B) fraction - older(A) fraction
```

had approximately:

```text
mean = 0.07136
sd   = 0.05598
n    = 32 runner blocks
```

These values are used only as a design prior / residual model.

They are not promoted to a HYP-002 finding.

## Candidate designs

One trial per factorial cell:

```text
D1  8 blocks  x 8 cells = 64 trials
D2 12 blocks  x 8 cells = 96 trials
D3 16 blocks  x 8 cells = 128 trials
D4 20 blocks  x 8 cells = 160 trials
```

## Monte Carlo stress

For each candidate, resample the observed runner residual distribution while attenuating the exploratory mean effect to:

```text
100%
75%
50%
35%
```

The design diagnostic reports:

- probability that a one-sided block-level t proxy detects a positive effect;
- P90 absolute estimation error of the mean residency contrast.

The t-test is a design approximation only.

The eventual HYP-002 inference remains a randomization/sign-flip analysis.

## Selection rule

Prefer the smallest design that:

1. has at least 90% screened detection probability at 50% of the exploratory effect;
2. does not pay many extra runner trials for only marginal gain;
3. preserves independent runner replication.

No weighted overall score is used.

## Authority boundary

The design Monte Carlo does not establish that recency causes residency selection.

It only allocates evidence for HYP-002.
