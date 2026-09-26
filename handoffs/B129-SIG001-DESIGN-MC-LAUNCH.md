# Bounce Handoff

> **Bounce ID:** B129
> **Status:** COMPLETE / SIG-001 DESIGN-MC LAUNCHED BY WORKFLOW COMMIT

## Objective

Launch only the frozen SIG-001 calibration design Monte Carlo after B128 CI PASS.

## Added

- `.github/workflows/sig-001-design-mc.yml`

The workflow uses:

- checkout@v7;
- setup-python@v7;
- upload-artifact@v7;
- `specs/SIG-001-DESIGN-MC.json`;
- `finite_ram_lab.sig001_design_mc`;
- 100,000 action-cost bootstrap resamples;
- 20,000 calibration Monte Carlo repetitions per scenario/sample-size cell.

## Launch semantics

Launch commit: `88853f3af6b785713f03048360522d06289aface`

The workflow's own push-path filter matches this commit and launches SIG-001 Design-MC exactly once.

## Next action

In a fresh bounce, discover the workflow run created by this commit exactly once and checkpoint its run ID/status.

Do not poll repeatedly.

## Authority boundary

Calibration design Monte Carlo only.
No predictor or memory intervention is authorized.
