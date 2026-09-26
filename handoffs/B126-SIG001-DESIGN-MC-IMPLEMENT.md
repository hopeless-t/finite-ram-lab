# Bounce Handoff

> **Bounce ID:** B126
> **Status:** COMPLETE / SIG-001 DESIGN-MC IMPLEMENTED

## Objective

Implement only the frozen B125 calibration design Monte Carlo.

## Completed

- `src/finite_ram_lab/sig001_design_mc.py`
- `tests/test_sig001_design_mc.py`

## Implemented contract

- exact one-sided Clopper-Pearson lower bounds;
- Bonferroni component alpha derived from family-wise 0.05;
- runner-block bootstrap of EXP-003 benefit/harm ratio;
- invalid bootstrap signs mapped to zero ratio for fail-closed lower-tail handling;
- log/geometric primary admission surface;
- arithmetic secondary surface;
- ACT certification simulation across frozen q/t/s scenarios and sample-size grid;
- unsafe-control false-certification check;
- ABSTAIN represented by NO-ACT accounting.

## Explicit non-work

The SIG-001 design Monte Carlo has not been launched.

No predictor or PAGEOUT experiment was added.

## Next action

Read ordinary CI for this implementation exactly once in a fresh bounce.

If PASS, launch only the frozen SIG-001 design Monte Carlo.

## Authority boundary

Implementation only.
