# MC-QUALITY-001 — Deep Monte Carlo Quality Loop

> **Status:** FROZEN SUPPORTING WORKFLOW

## Principle

More computation is useful only when it buys one of three things:

1. lower uncertainty;
2. better parameter-space coverage;
3. better knowledge of rare failure regimes.

Raw trial count is not itself a quality metric.

## Automated calculations

MC-QUALITY-001 extends MC-001 with a larger scheduled sample and computes:

- bootstrap 95% confidence intervals for the mean gap;
- bootstrap intervals for p90 and p99;
- Wilson intervals for a declared rare-gap event;
- convergence of the mean across increasing sample sizes;
- stratified summaries by capacity/universe ratio.

The initial rare-gap event is:

```text
fault_rate_gap >= 0.20
```

## Why deeper runs help

For stable independent sampling, uncertainty around a mean typically shrinks on the order of:

```text
1 / sqrt(n)
```

so doubling compute does not halve uncertainty.

The workflow therefore tracks uncertainty width, not only trial count.

## Automation role

The scheduled workflow is decision support. It may identify families that remain unstable, rare regimes that need more samples, and parameter ranges worth promoting into hosted controlled experiments.

It does not automatically promote synthetic evidence into a Linux finding.

## Stop-rule principle

The right stopping question is not “have we run enough trials?”

It is:

> Is the remaining uncertainty small enough for the next research decision?
