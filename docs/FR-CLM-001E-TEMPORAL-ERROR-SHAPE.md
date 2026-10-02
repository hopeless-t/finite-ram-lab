# FR-CLM-001E — Matched-Marginal Temporal Error Shape

Status: **SYNTHETIC TEMPORAL-DEPENDENCE QUALIFICATION**

## Goal

FR-CLM-001D established that one-step and endpoint-only correctness can hide
trajectory damage.

FR-CLM-001E asks whether a marginal error rate is itself enough to describe
trajectory risk.

The experiment holds the expected relevance-label flip rate at 1% while
changing how those flips are correlated.

## Frozen environment

- resident budget: 4
- trajectory length: 64
- replicates: 8,192
- required-state refresh: every 8 steps
- distractors: 2 per step
- expected marginal label-flip rate: 1%

## Arms

### IID_EVENT

Every candidate-event relevance decision flips independently with probability
0.01.

This spreads error opportunities broadly across trajectories and steps.

### STEP_SHARED

Each step independently becomes a bad step with probability 0.01.

On a bad step, every candidate-event relevance label flips together.

The per-label marginal remains approximately 1%, but within-step correlation is
maximal.

### MARKOV_BURST

A two-state GOOD/BAD process has stationary BAD probability 0.01.

Frozen transitions:

- BAD -> BAD = 0.75
- GOOD -> BAD = 0.0025252525252525255

While BAD, all candidate-event labels flip together.

This preserves the 1% stationary marginal while adding temporal persistence.

## Why this matters

Three processes can have the same average label-flip frequency but distribute
risk differently:

- many trajectories with shallow damage;
- fewer trajectories with synchronized damage;
- rare trajectories with persistent deep damage.

Therefore the mean error rate is not a complete failure model.

## Primary endpoints

- observed label-flip rate;
- trajectory survival rate;
- affected-trajectory rate;
- conditional p95 maximum consecutive failure run.

## Secondary endpoints

- endpoint success;
- mean per-step exactness;
- conditional mean maximum failure run;
- conditional mean failed steps;
- first-failure histogram.

## Frozen falsifiers

Qualification requires:

- every arm's observed label-flip rate in [0.009, 0.011];
- trajectory survival ordering:
  `IID_EVENT < STEP_SHARED < MARKOV_BURST`;
- IID affects more than 60% of trajectories;
- STEP_SHARED affects 40–60%;
- MARKOV_BURST affects fewer than 25%;
- MARKOV_BURST conditional p95 failure-run length >= 12;
- MARKOV_BURST conditional mean maximum failure run > IID_EVENT;
- endpoint success >= 0.98 in every arm.

The apparent paradox is intentional:

a temporally clustered process may damage fewer trajectories because errors are
concentrated, while producing much deeper damage when it does hit.

## Interpretation boundary

The controlled variable is the **marginal relevance-label flip rate**, not the
semantic failure rate.

Semantic consequences are allowed to differ. That difference is the object of
the experiment.

## Claim ceiling

**SYNTHETIC_TEMPORAL_ERROR_SHAPE_ONLY**

No real model, provider, CLM, Pi, or KITten error process is measured.

## Next if PASS

FR-CLM-001F should move from fixed synthetic correlations to estimation:

- infer latent bad-state persistence from observed failure sequences;
- compare IID vs hidden-state likelihood;
- estimate whether a real trace is compatible with bursty failure;
- preserve first-failure and recovery evidence.

That would turn the synthetic finding into a trace-analysis tool for later real
context-manager experiments.
