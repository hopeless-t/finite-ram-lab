# EXP-003 Design Monte Carlo Implementation

> **Status:** IMPLEMENTED / NOT YET EXECUTED

## Frozen model

Candidate designs:

- D1: 16 blocks × 1 complete repeat = 384 trials;
- D2: 24 × 1 = 576;
- D3: 32 × 1 = 768;
- D4: 16 × 2 = 768;
- D5: 24 × 2 = 1152.

Capture scenarios:

- 0%;
- 25%;
- 50%;
- 75%.

## Empirical simulation

HYP-003 remains the benefit-model source.

For each runner-block × pressure stratum, the compact input contains the mean and sample SD of exactly two HYP-003 observations. The simulation reconstructs the corresponding two-point empirical residual distribution and bootstraps it rather than inventing Gaussian latency noise.

New runner blocks are sampled from the 16 observed HYP-003 runner profiles.

CORRECT_PAGEOUT capture is modeled as a prospective shift of the naturally misaligned log-latency mean toward the aligned mean by the frozen capture fraction.

## Screening inference

Design power ranking uses a one-sided paired t screen on runner-block log-latency contrasts, matching existing repository design-MC practice.

This is **not** the final EXP-003 inference.

The real experiment remains pre-registered for block sign-flip inference.

## Frozen selection rule

A design is eligible only if:

- null false-positive rate <= 0.065;
- 25% capture detection >= 0.70;
- 50% capture detection >= 0.90.

Choose the eligible design with the fewest trials; break ties in favor of more independent runner blocks.

If none qualify, fail closed.

## Red-Team calibration

EXP-002 at 164 MiB is reported separately for:

- wrong-vs-correct HOT-latency stress;
- wrong-vs-nohint HOT-latency stress;
- correct-vs-nohint total interval;
- PAGEOUT advice cost.

It is not pooled into the HYP-003 160–162 MiB benefit model.
