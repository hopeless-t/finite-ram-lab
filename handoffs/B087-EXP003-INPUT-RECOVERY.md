# Bounce Handoff

> **Bounce ID:** B087
> **Status:** COMPLETE / B086 INPUT SNAPSHOT RECOVERED

## Objective

Reconcile B086 after verification found that its two CSV payloads accidentally contained a file-visibility error string rather than empirical data.

## Verification

B086 provenance was correct, but both CSV blobs had identical incorrect content and therefore were not usable design inputs.

This bounce replaces them with one compact, self-contained JSON snapshot derived from the already downloaded canonical artifacts.

## Canonical input

- `analysis/inputs/EXP-003-DESIGN-empirical-inputs.json`

It contains:

- 32 HYP-003 runner-block × MemoryHigh strata;
- 60 EXP-002 runner-block × arm strata;
- source run IDs;
- source artifact IDs;
- source artifact SHA-256 values;
- source trial CSV SHA-256 values.

## Cleanup

The two invalid B086 CSV files and the superseded standalone provenance JSON are removed from the current tree.

B086 remains audit history.

## Boundary

Recovered input only. No new scientific evidence and no EXP-003 allocation decision.

## Next action

Implement only the EXP-003 design Monte Carlo over D1-D5 and the frozen capture scenarios.
