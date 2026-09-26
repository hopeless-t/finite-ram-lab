# GATE-001 Empirical Policy Analysis

> **Status:** IMPLEMENTED / NOT YET EXECUTED

The calculator implements the B107 selective ACT/NO-ACT policy exactly.

## State/action mapping

Correct signal:

- aligned -> NO_HINT;
- misaligned -> CORRECT_PAGEOUT.

Wrong/stale signal:

- aligned -> WRONG_PAGEOUT;
- misaligned -> NO_HINT.

## Metrics

Two surfaces remain separate:

- arithmetic total-work cost;
- log/geometric total-work cost.

## Break-even

For each misalignment prevalence q, the calculator solves the empirical semantic-signal accuracy threshold against NO_HINT and propagates uncertainty with 100,000 runner-cluster bootstrap resamples.

## Boundary

This analysis does not execute a gate and does not estimate production q.
