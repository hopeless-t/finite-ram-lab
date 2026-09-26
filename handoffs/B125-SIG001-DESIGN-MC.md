# Bounce Handoff

> **Bounce ID:** B125
> **Status:** COMPLETE / SIG-001 DESIGN-MC CONTRACT FROZEN

## Frozen artifacts

- `specs/SIG-001-DESIGN-MC.json`
- `docs/SIG-001-DESIGN-MC.md`

## Contract

SIG-001 uses:

- exact one-sided Clopper-Pearson lower bounds for q, sensitivity and specificity;
- a conservative lower bootstrap quantile for the EXP-003 benefit/harm ratio;
- Bonferroni family-wise alpha = 0.05 across four uncertainty components;
- log/geometric total-work as the primary admission surface;
- arithmetic total-work as secondary evidence;
- 20,000 Monte Carlo repetitions for each scenario/sample-size cell;
- explicit low-q unsafe and safe controls.

ABSTAIN maps to NO-ACT.

## Explicit non-work

- no predictor training;
- no production prevalence estimate;
- no PAGEOUT execution;
- no deployed gate.

## Next action

Implement only the frozen SIG-001 design Monte Carlo and unit tests.

## Authority boundary

Calibration-design analysis only.
