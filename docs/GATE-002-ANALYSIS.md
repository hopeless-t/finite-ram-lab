# GATE-002 Class-Conditional Policy Frontier

> **Status:** FROZEN DESIGN / NOT YET IMPLEMENTED

## Question

What specificity is required for a selective ACT/NO-ACT gate to beat NO_HINT at a given:

- true misalignment prevalence `q`;
- sensitivity `t = P(ACT | truly misaligned)`?

## Empirical primitives

Reuse the frozen GATE-001 input derived from randomized EXP-003 runner blocks.

For each metric:

- `h = A_W - A_N`: aligned-state wrong-action harm;
- `b = M_N - M_C`: misaligned-state correct-action benefit.

The gate beats NO_HINT when:

`q*t*b > (1-q)*(1-s)*h`

Therefore the point minimum-specificity frontier is:

`s* = 1 - q*t*b / ((1-q)*h)`

when `h > 0` and `b > 0`.

## Frozen analysis

- q grid: 0.10 / 0.25 / 0.50 / 0.75 / 0.90;
- sensitivity grid: 0.50 through 1.00 using the frozen GATE-001 accuracy grid;
- arithmetic and log/geometric total-work surfaces remain separate;
- 100,000 runner-cluster bootstrap resamples;
- report point frontier, bootstrap median, 95% interval, and valid/sign-stable fraction;
- preserve raw thresholds and a clipped [0,1] operational view separately.

## Interpretation boundary

This analysis does not estimate production prevalence, sensitivity, or specificity.

It does not define a predictor and does not authorize ACT.

Its purpose is to expose the class-conditional reliability contract implied by the observed asymmetric action costs.
