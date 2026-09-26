# SIG-001 Semantic Signal Calibration — Design Monte Carlo

> **Status:** FROZEN DESIGN / NOT YET IMPLEMENTED

## Purpose

Estimate how many labeled calibration windows are required before a fail-closed semantic signal provider can be admitted against the empirical GATE-002 action-cost frontier.

This is a calibration-design study, not predictor training.

## Signal semantics

For each calibration window, the provider emits either:

- ACT; or
- NO-ACT / ABSTAIN.

ABSTAIN is mapped to NO-ACT for safety accounting.

After the future demand is realized, the window is labeled truly:

- misaligned; or
- aligned.

The calibrated quantities are:

- `q = P(misaligned)`;
- `t = P(ACT | misaligned)` — sensitivity;
- `s = P(NO-ACT or ABSTAIN | aligned)` — specificity.

## Fail-closed admission rule

Use a family-wise error budget of 0.05 split equally by Bonferroni across four uncertainty components:

1. lower bound for q;
2. lower bound for sensitivity;
3. lower bound for specificity;
4. lower bound for empirical benefit/harm ratio from EXP-003.

For binomial quantities, use exact one-sided Clopper-Pearson lower bounds.

For the empirical action-cost ratio:

- `h = A_W - A_N`;
- `b = M_N - M_C`;
- `r = b / h`.

Use the frozen runner-block bootstrap to obtain a conservative lower quantile `r_L`.

The conservative required specificity is:

`s_required = 1 - (q_L * t_L * r_L) / (1 - q_L)`

with fail-closed handling for zero/invalid denominators or invalid action-cost signs.

Admit only when:

`s_L > s_required`

The log/geometric total-work surface is primary.
Arithmetic total-work is secondary evidence and may not override a primary failure.

## Monte Carlo

For every frozen scenario and sample size:

1. draw the number of truly misaligned windows;
2. draw ACT successes among misaligned windows;
3. draw NO-ACT/ABSTAIN successes among aligned windows;
4. compute exact one-sided lower bounds;
5. apply the conservative empirical frontier;
6. record certification rate and admission-margin distribution.

Safe-candidate scenarios report the minimum N reaching at least 80% certification probability.

Unsafe-control scenarios must remain at or below 5% false certification across the tested sample-size grid.

## Why low-q is explicit

GATE-002 shows that low misalignment prevalence is the regime in which false ACT on aligned states imposes the strongest specificity requirement.

The design therefore includes both borderline and strong low-q providers plus an unsafe low-q control.

## Boundaries

The Monte Carlo does not:

- select or train a predictor;
- estimate real production q;
- establish exchangeability in any future workload;
- execute PAGEOUT;
- authorize a deployed gate.

It only sizes a future observational calibration dataset and stress-tests the admission rule.
