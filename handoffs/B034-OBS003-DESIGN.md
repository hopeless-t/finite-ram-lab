# Bounce Handoff

> **Bounce ID:** B034  
> **Status:** COMPLETE

## Objective

Read the OBS-003 design Monte Carlo and freeze a Pareto-efficient natural-misalignment observation design.

## Evidence

Design run:

- run: `36242326971`;
- 10,000 simulated experiments per design/scenario;
- four transition / runner-heterogeneity scenarios.

Pareto set:

```text
D1_12x4
D4_32x2
```

Selected:

```text
D4_32x2
```

## Frozen design

- 32 independent runner blocks;
- MemoryHigh levels: 160, 162, 164, 166, 168 MiB;
- 2 repeats per level per block;
- 320 total NO_HINT trials;
- MemoryMax 320 MiB;
- no application hint or intervention.

Primary quantity:

```text
P(HOT resident fraction < 1.0 immediately before reuse)
```

## Why D4

D4 used the same 320-trial budget as D2 while improving simulated prevalence/curve error through greater independent runner replication.

D3 used more trials and was dominated on the declared error criteria.

D1 was cheaper but materially weaker in worst-case error and affected-runner coverage.

## Repository updates

- `findings/OBS-003-design-study.md`
- `specs/OBS-003.json`
- `docs/OBS-003.md`

## Next recommended bounce

> Implement OBS-003 using the existing NO_HINT semantic workload, validate scheduling/aggregation, launch exactly the frozen 320-trial study, write a launch handoff, and stop.

## Authority boundary

The design Monte Carlo does not establish the real natural misalignment curve.
