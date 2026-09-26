# VAL-003 Design Council — Catastrophic Tail Risk

> **Status:** DESIGN STUDY

## Confirmatory question

Using **independent new data**, does CORRECT_PAGEOUT reduce the probability of a HOT-retouch stall of at least 500 ms relative to NO_HINT under the same 164 MiB transition-zone workload?

## Why this is a new study

EXP-002 did not pre-register a tail-risk endpoint.

The 500 ms endpoint is therefore fixed **before** VAL-003 data collection.

The threshold is motivated by:

- OBS-001's original ~486.7 ms retouch stall;
- CHAR-001's ~0.8–1.0 s pressured regime;
- exploratory EXP-002 separation in the far tail.

EXP-002 trials are not confirmatory samples.

## Pseudo-Council

### Statistics reviewer

This is a rare-event, clustered design.

Runner identity must remain the replication block.

Each block runs repeated CORRECT_PAGEOUT and NO_HINT trials.

Primary block outcome:

    catastrophic-event rate(CORRECT)
      - catastrophic-event rate(NO_HINT)

### Falsification reviewer

Do not choose a lower threshold after seeing new data.

If 500 ms events are too rare to identify a difference, the study may be inconclusive; that is valid.

### Performance reviewer

Retain continuous tail summaries as secondary diagnostics, but the pre-registered primary endpoint is the >=500 ms event.

### Robustness reviewer

WRONG_PAGEOUT is not repeated here. EXP-002 already established large wrong-hint harm.

Spend the new evidence budget on CORRECT versus NO_HINT tail risk.

### Monte Carlo reviewer

Stress the design under:

- shared runner heterogeneity;
- arm-specific runner variation;
- baseline catastrophic rates around 3–8%;
- target reductions from 5%→2.5% and 5%→1%.

Candidate designs:

    D1: 20 blocks x 20 repeats/arm = 800 trials
    D2: 32 blocks x 12 repeats/arm = 768 trials
    D3: 40 blocks x 10 repeats/arm = 800 trials
    D4: 40 blocks x 16 repeats/arm = 1280 trials

## Planned confirmatory inference

If the selected design has more than 20 runner blocks, use a deterministic Monte Carlo sign-flip randomization test with at least 1,000,000 sign vectors and a fixed seed.

Report Monte Carlo standard error for the randomization p-value.

Use a cluster bootstrap over runner blocks for the paired absolute risk difference.

## Authority boundary

A positive VAL-003 result would support reduction of catastrophic tail risk for this specific correct semantic PAGEOUT mechanism.

It would not by itself justify a generalized coordination plane.
