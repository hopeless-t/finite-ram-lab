# EXP-003 Design Monte Carlo — Structured Calibration Readback

> **Status:** STRUCTURED RESULT VERIFIED
> **Run:** 36253106666
> **Artifact:** 10909658213 / EXP-003-DESIGN-36253106666

## Selection verification

Structured result confirms:

- selected design: `D1_16x1`;
- 16 runner blocks;
- one complete repeat;
- 384 total trials.

D1:

- null FP: 0.0428;
- 25% capture detection: 0.9990;
- 50% capture detection: 0.9998;
- 75% capture detection: 1.0000.

Median simulated CORRECT/NO_HINT HOT-latency ratio:

- 0% capture: 0.999;
- 25% capture: 0.331;
- 50% capture: 0.111;
- 75% capture: 0.037.

## Separate EXP-002 Red-Team calibration

These values come from EXP-002 at 164 MiB and are **not pooled** into the HYP-003 160–162 MiB benefit model.

PAGEOUT call cost for the CORRECT arm:

- median runner-block mean advice time: 14.27 ms;
- p90 runner-block mean advice time: 30.05 ms.

CORRECT vs NO_HINT total interval:

- geometric mean ratio: 0.932;
- median block ratio: 0.903.

WRONG vs CORRECT HOT-retouch latency:

- geometric mean ratio: 35.64×;
- median block ratio: 94.86×.

WRONG vs NO_HINT HOT-retouch latency:

- geometric mean ratio: 32.19×;
- median block ratio: 64.52×.

## Interpretation

The calibration does not contradict D1 selection.

It reinforces the requirement that EXP-003 preserve:

- WRONG_PAGEOUT as a mandatory Red-Team arm;
- total-interval accounting;
- aligned trials as unnecessary-action controls;
- HOT-retouch and total-cost outcomes as separate claims.

The large wrong-action asymmetry remains a central falsification constraint.

## Authority boundary

This is design calibration only.

It does not establish that PAGEOUT is beneficial at 160–162 MiB and does not authorize deployment.
