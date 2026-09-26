# Bounce Handoff

> **Bounce ID:** B096
> **Status:** COMPLETE / EXP-003 EXECUTABLE DESIGN FROZEN

## Objective

Run the final design Council after design-MC and Red-Team calibration and freeze or reject the EXP-003 executable contract.

## Decision

Freeze EXP-003.

Allocation:

- 16 independent runner blocks;
- one complete 24-cell factorial repeat;
- 384 total trials.

Factors:

- MemoryHigh 160 / 162 MiB;
- initial fault order lower→upper / upper→lower;
- future HOT lower / upper;
- CORRECT_PAGEOUT / NO_HINT / WRONG_PAGEOUT.

## Primary benefit question

In naturally misaligned trials:

> Does CORRECT_PAGEOUT reduce HOT-retouch latency versus NO_HINT?

Primary inference:

- runner-block mean log contrast;
- exact one-sided 2^16 sign-flip;
- 20,000 runner-cluster bootstrap.

## Net-benefit constraint

Total work interval includes:

- advice;
- burst;
- HOT retouch.

HOT-retouch benefit without total-work benefit is only cost shifting.

## Red Team

WRONG_PAGEOUT comparisons are mandatory for HOT-retouch and total-work endpoints.

Aligned trials remain mandatory control strata.

## GitHub artifacts

- `docs/EXP-003.md`
- `specs/EXP-003.json`

## Next action

Implement only the EXP-003 shared-VMA workload and its fail-closed trial checks.

Do not implement analysis or workflow in the same bounce.

## Authority boundary

Design is frozen. The experiment is not yet launched.
