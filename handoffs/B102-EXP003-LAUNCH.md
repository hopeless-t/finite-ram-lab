# Bounce Handoff

> **Bounce ID:** B102
> **Status:** COMPLETE / EXP-003 LAUNCHED BY WORKFLOW COMMIT

## Objective

Create and launch the frozen EXP-003 16-block / 384-trial experiment.

## Added

- `.github/workflows/exp-003.yml`

The workflow exactly uses:

- 16 independent runner blocks;
- one 24-cell factorial repeat per block;
- MemoryHigh 160 / 162 MiB;
- CORRECT_PAGEOUT / NO_HINT / WRONG_PAGEOUT;
- shared-VMA initial-fault and future-HOT factors;
- frozen aggregate analysis.

## Launch semantics

This commit matches the workflow's own push-path filter and launches EXP-003.

## Next action

Discover the EXP-003 workflow run created by this commit exactly once and checkpoint its run ID/status.

Do not poll repeatedly.

## Authority boundary

Experiment launched; no result exists yet.
