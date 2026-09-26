# EXP-002 Design Council — Semantic PAGEOUT Value

> **Status:** DESIGN STUDY

## Research question

Can application knowledge about a not-soon-needed region improve behavior under **natural** transition-zone pressure using only an existing Linux userspace interface?

## Arms

All arms use two 32 MiB semantic regions plus a 96 MiB burst at MemoryHigh 164 MiB.

The future workload always retouches HOT.

### CORRECT_PAGEOUT

Prepare the first 16 MiB of COLD with `MADV_PAGEOUT` before the burst.

### WRONG_PAGEOUT

Prepare the first 16 MiB of HOT before the burst.

### NO_HINT

No advice before the burst.

## Pseudo-Council

### Application/runtime reviewer

This is the first direct value-of-semantic-information experiment.

The semantic fact is only:

> which equal-size region will not be needed in the next phase?

### Kernel / VM reviewer

Do not call proactive `memory.reclaim`.

The burst must create the same natural memcg pressure used in the observational transition studies.

### Performance reviewer

Record two different outcomes rather than hiding a trade-off:

1. HOT retouch latency — mechanism-sensitive next-use cost;
2. total hint-to-HOT-completion interval — includes PAGEOUT preparation cost.

A hint that merely moves latency earlier is not automatically a net win.

### Measurement reviewer

Record HOT/COLD residency after the burst before HOT retouch.

This is mediator evidence, not the primary performance outcome.

### Falsification / Red-Team reviewer

WRONG_PAGEOUT is required.

A useful semantic mechanism should show directional coherence:

    CORRECT better than NO_HINT
    WRONG worse than CORRECT

at least for the mechanism-sensitive outcome.

### Statistics reviewer

Runner is the replication block.

Primary pre-registered contrast:

    CORRECT_PAGEOUT vs NO_HINT

on mean log HOT-retouch latency within block.

Final inference should use a block sign-flip test.

WRONG_PAGEOUT is a pre-registered directional validation arm, analyzed separately.

## Design Monte Carlo model

Use the already-observed heavy-tailed 164 MiB behavior as the qualitative template:

- fast state around a few milliseconds;
- slow state around hundreds of milliseconds;
- runner-level heterogeneity;
- additional extreme tail.

Model baseline slow-branch probability as 0.25 and screen designs under correct-hint branch probabilities:

    null     0.25
    modest   0.15
    material 0.10
    strong   0.05

Candidate designs:

    D1 16 blocks x 4 repeats/arm = 192 trials
    D2 20 blocks x 4 repeats/arm = 240 trials
    D3 20 blocks x 6 repeats/arm = 360 trials
    D4 24 blocks x 4 repeats/arm = 288 trials

## Authority boundary

A positive experiment would support value of one concrete application semantic signal through one existing Linux mechanism.

It would still not justify a generalized coordinator without further cost, robustness, and stale/wrong-hint studies.
