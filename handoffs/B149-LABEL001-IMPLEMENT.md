# Bounce Handoff

> **Bounce ID:** B149
> **Status:** COMPLETE / LABEL-001 ANALYZER IMPLEMENTED

## Completed

- `src/finite_ram_lab/label001.py`
- `tests/test_label001.py`

## Implementation

The analyzer:

- verifies the frozen `trials.csv` SHA-256 before analysis;
- filters to NO_HINT and frozen 160/162 MiB pressure levels;
- requires the frozen runner-block/trial counts;
- defines whole-region natural misalignment by HOT residency < COLD residency;
- treats exact ties as AMBIGUOUS;
- reports confusion/prevalence/sensitivity/specificity/agreement;
- uses runner-block bootstrap for uncertainty;
- reports pressure-stratified descriptives;
- computes a continuous residency-gap association with log HOT-retouch;
- keeps first-16-MiB results secondary.

The Spearman interval uses a runner-block bootstrap over a frozen pooled-rank transform so 100,000 resamples remain bounded in cost.

## Tests

Coverage includes:

- expected confusion behavior;
- mechanism-direction check;
- digest mismatch fail-closed;
- intervention-arm exclusion;
- exact tie handling.

## Next action

Read ordinary CI triggered by B149 exactly once.

If SUCCESS, launch only the bounded offline LABEL-001 analysis.

## Authority boundary

Retrospective analysis implementation only.
No provider or memory action is authorized.
