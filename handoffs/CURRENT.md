# CURRENT

> **Latest bounce:** B170
> **Stage:** STRATA-001 / PILOT AGGREGATE PATH FIX, CI PENDING

## Reconciled pilot

- pilot run: `36336994450`
- all six block jobs: SUCCESS
- aggregate job: FAILURE
- cause: downloaded artifact directory name not recognized

## Fix

Collector now accepts `strata001-pilot-block-*`.

## Next action

Read ordinary CI for B170 exactly once.

- SUCCESS → recover and aggregate the existing six block artifacts; do not re-run trials.
- pending → checkpoint EXTERNAL_WAIT.
- failure → inspect failure only.

## Attribution

Inspired by Niko1221/Strata; independent implementation.

## Authority boundary

Pilot recovery only.
