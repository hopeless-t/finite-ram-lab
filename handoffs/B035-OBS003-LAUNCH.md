# Bounce Handoff

> **Bounce ID:** B035  
> **Status:** COMPLETE / COMPUTE LAUNCHED

## Objective

Implement and launch the frozen OBS-003 natural residency-misalignment map exactly as selected by the design Monte Carlo.

## Canonical inputs

- `handoffs/B034-OBS003-DESIGN.md`
- `findings/OBS-003-design-study.md`
- `specs/OBS-003.json`
- `docs/OBS-003.md`

## Completed

- implemented a NO_HINT-only OBS-003 workload wrapper;
- implemented balanced 32-block / five-level scheduling;
- implemented runner-cluster bootstrap prevalence analysis;
- implemented conditional residency/latency diagnostics;
- added schedule tests;
- launched the frozen 320-trial study.

## Frozen study

```text
32 independent runner blocks
levels = 160, 162, 164, 166, 168 MiB
2 trials / level / block
320 total trials
NO_HINT only
```

Primary observable:

```text
HOT resident fraction < 1.0 immediately before reuse
```

## Workflow

- launch commit: `987fedf5b27755dc7264d4a9b27f58207b1d1be7`
- run: `36242552339`

## Next recommended bounce

> Read OBS-003 using the frozen prevalence analysis, write the finding, decide whether a formal decision-headroom / Value-of-Information study is warranted, update GitHub, and stop.

## Authority boundary

Launching OBS-003 is not evidence that natural residency selection is good or bad.

The study measures opportunity frequency; it does not test an intervention.
