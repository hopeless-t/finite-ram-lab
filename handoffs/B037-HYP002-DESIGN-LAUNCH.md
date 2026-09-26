# Bounce Handoff

> **Bounce ID:** B037  
> **Status:** COMPLETE / DESIGN COMPUTE LAUNCHED

## Objective

Choose a runner-block allocation for a balanced factorial HYP-002 test of past recency/order versus future semantic HOT identity at 160–162 MiB.

## Canonical inputs

- `handoffs/B036-OBS003-FINDING.md`
- `findings/OBS-003-initial.md`
- `docs/HYP-002-DESIGN.md`

## Factorial question

Randomize independently:

- recent identity A/B;
- future HOT identity A/B;
- MemoryHigh 160/162 MiB.

Both regions receive equal touch counts.

Primary block contrast:

```text
recent resident fraction - older resident fraction
```

before HOT reuse.

Key secondary contrast:

```text
HOT=older versus HOT=recent retouch latency
```

## Design screen

Candidate designs:

```text
D1  8 blocks  x 8 cells = 64 trials
D2 12 blocks  x 8 cells = 96 trials
D3 16 blocks  x 8 cells = 128 trials
D4 20 blocks  x 8 cells = 160 trials
```

The Monte Carlo uses the exploratory OBS-003 runner-block recency contrast as a residual model and stresses attenuation to 100%, 75%, 50%, and 35% of the observed mean effect.

Selection target:

> smallest design with at least 90% screened detection probability at 50% of the exploratory effect.

The design-screen t statistic is only an allocation proxy. Final HYP-002 inference remains runner-block randomization/sign-flip.

## Workflow

- design workflow commit: `a956fe10057e87991506aac7a2fbfd7bd74723ca`
- run: `36242981650`

## Next recommended bounce

> Read the design Monte Carlo, freeze the smallest qualifying design, commit the HYP-002 spec/contract, and stop before experiment launch.

## Authority boundary

The design Monte Carlo does not establish a recency effect.
