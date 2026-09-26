# Bounce Handoff

> **Bounce ID:** B038  
> **Status:** COMPLETE

## Objective

Read the HYP-002 design Monte Carlo and freeze the smallest design that meets the pre-declared half-effect sensitivity target.

## Evidence

Design run:

- run: `36242981650`;
- 20,000 simulations per design/attenuation scenario;
- empirical residual model from exploratory OBS-003 160/162 MiB runner-block recency contrasts.

Screened detection probability at 50% of the exploratory effect:

```text
D1_8   0.712
D2_12  0.757
D3_16  0.918
D4_20  0.944
```

Pre-declared target:

```text
>= 0.90
```

## Frozen design

Selected:

```text
D3_16
```

Study:

- 16 independent runner blocks;
- 2 MemoryHigh levels: 160 / 162 MiB;
- recent identity A/B;
- future HOT identity A/B;
- 8 factorial cells per block;
- 128 total trials;
- no hint/intervention.

Primary block contrast:

```text
mean(recent resident fraction - older resident fraction)
```

Primary inference:

- exact one-sided sign-flip over `2^16 = 65,536` assignments;
- runner-cluster bootstrap interval.

Key secondary:

```text
HOT=older versus HOT=recent retouch latency
```

## Repository updates

- `findings/HYP-002-design-study.md`
- `specs/HYP-002.json`
- `docs/HYP-002.md`

## Next recommended bounce

> Implement HYP-002 exactly as frozen, add known-balance tests, launch the 128-trial factorial study, write the launch handoff, and stop.

## Authority boundary

The design Monte Carlo is sampling decision support only.

It does not establish a recency effect or semantic information value.
