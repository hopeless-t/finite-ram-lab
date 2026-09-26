# Bounce Handoff

> **Bounce ID:** B039  
> **Status:** COMPLETE / COMPUTE LAUNCHED

## Objective

Implement and launch the frozen HYP-002 factorial experiment without changing the design after data collection begins.

## Canonical inputs

- `handoffs/B038-HYP002-DESIGN.md`
- `findings/HYP-002-design-study.md`
- `specs/HYP-002.json`
- `docs/HYP-002.md`

## Completed

- implemented equal-touch recency-order workload;
- implemented direct A/B mincore residency observation;
- implemented full 2 x 2 x 2 factorial scheduling;
- implemented exact 2^16 block sign-flip primary inference;
- implemented cluster-bootstrap residency interval;
- implemented pre-registered semantic-alignment latency secondary;
- added factorial schedule tests;
- launched the frozen 128-trial study.

## Frozen study

```text
16 independent runner blocks

MemoryHigh:
160 / 162 MiB

recent identity:
A / B

future HOT identity:
A / B

8 cells per block
128 total trials
```

No memory-management hint or intervention is used.

## Workflow

- launch commit: `79164932d214cd274e40620e8f1e073aaa5b9903`
- run: `36243199948`

## Next recommended bounce

> Read HYP-002 using only the frozen primary and secondary analyses, record the information-gap finding, update repository status, write the next handoff, and stop.

## Authority boundary

Launching HYP-002 is not evidence that recency determines residency or that future semantic information has performance value.
