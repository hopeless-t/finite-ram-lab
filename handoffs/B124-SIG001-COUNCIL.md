# Bounce Handoff

> **Bounce ID:** B124
> **Status:** COMPLETE / SIG-001 CALIBRATION COUNCIL CONVERGED

## Trigger

B123 showed that a safe selective gate requires class-conditional reliability, not a single aggregate accuracy number.

## Fresh exploration

Two external patterns matter:

1. Linux DAMON provides lightweight access-pattern monitoring and access-aware actions, but it remains an observation/history mechanism. It does not by itself provide application-semantic knowledge of future HOT demand.
   - https://docs.kernel.org/mm/damon/design.html
   - https://www.kernel.org/doc/html/latest/admin-guide/mm/damon/reclaim.html

2. Recent selective-prediction work formalizes a reject/abstain option with calibrated risk control rather than forcing a decision on every sample.
   - https://arxiv.org/abs/2603.24704
   - https://arxiv.org/abs/2506.21802

## Atomic deduction from EXP-003

EXP-003 randomized future HOT identity independently of initial fault order.

Therefore a predictor restricted to past OS/fault-order state cannot recover the missing future semantic variable by construction.

The information source required by GATE-002 must come from an application-semantic forecast/provider or another genuinely future-informative signal.

## Council convergence

### Statistics

Do not estimate one aggregate accuracy.

Calibrate separately:

- prevalence `q = P(truly misaligned)`;
- sensitivity `t = P(ACT signal | truly misaligned)`;
- specificity `s = P(NO-ACT signal | truly aligned)`;
- optional abstention/coverage if the provider can reject.

Use finite-sample one-sided bounds and fail closed.

### Systems

The next experiment should be observational/calibration-only.

No PAGEOUT action is required to measure semantic-provider reliability.

### Red Team

Low-q is the dangerous regime because false ACT on aligned states is expensive.

Admission must use conservative uncertainty directions:

- lower confidence bound for q;
- lower confidence bound for sensitivity;
- lower confidence bound for specificity;
- upper/conservative GATE-002 action-cost frontier.

### Authority

If the calibrated lower bounds do not clear the empirical frontier with margin, return NO-ACT/ABSTAIN.

No fallback to unconditional ACT.

### Economics

Before collecting a new large dataset, run a design Monte Carlo to estimate the sample size needed to certify or reject plausible signal-provider regimes.

## Decision

Create **SIG-001 — Semantic Signal Calibration**.

Phase 1 is design-only Monte Carlo.

Its purpose is to answer:

> Given true q, sensitivity and specificity, how many labeled calibration windows are needed before the fail-closed admission rule is likely to make a decision?

No predictor is chosen or trained in this phase.

## Next action

Freeze the SIG-001 design-Monte-Carlo contract.

The Monte Carlo must cover low-q stress explicitly and use the GATE-002 log/geometric frontier as the conservative primary admission surface while retaining arithmetic as secondary evidence.

## Authority boundary

Calibration research only.
No deployed gate, predictor commitment, or memory intervention is authorized.
