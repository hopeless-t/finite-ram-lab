# Bounce Handoff

> **Bounce ID:** B091
> **Status:** COMPLETE / DESIGN-MC LAUNCHED BY WORKFLOW COMMIT

## Objective

Launch only the frozen EXP-003 design Monte Carlo.

## Change

Added:

- `.github/workflows/exp-003-design-mc.yml`

The workflow uses:

- checkout@v7
- setup-python@v7
- upload-artifact@v7
- `specs/EXP-003-DESIGN-MC.json`
- `finite_ram_lab.exp003_design_mc`

## Launch semantics

This commit matches the workflow's own push-path filter and therefore launches the design study.

No EXP-003 scientific experiment is launched.

## Next action

In a fresh bounce, discover the workflow run created by this commit and record its run ID/status once.

Do not poll repeatedly.

## Authority boundary

Design Monte Carlo only.
