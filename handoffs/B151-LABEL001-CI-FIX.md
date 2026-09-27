# Bounce Handoff

> **Bounce ID:** B151
> **Status:** COMPLETE / LABEL-001 CI FAILURE RECONCILED AND FIXED

## Reconciled external run

B149 CI run `36292826020` completed with `failure`.

The only failing unit test was:

`test_tie_is_ambiguous`

## Root cause

The runner-block bootstrap called the full confusion-metric helper for each individual runner block.

That helper incorrectly required every single resampling unit to contain both observable classes.

This is stronger than the statistical contract.

Runner blocks are the cluster-resampling units; individual blocks may legitimately contain only one class, especially after exact ties are excluded as AMBIGUOUS.

## Fix

- separate raw confusion counts from metric calculation;
- bootstrap runner blocks from raw TP/FP/FN/TN sufficient statistics;
- require both classes only for the pooled primary estimate;
- allow pressure-stratified descriptive rows to report missing class-conditioned metrics as null rather than fail.

No scientific threshold, label definition, bootstrap seed, or source data changed.

## User-directed priority change

LABEL-001 remains the canonical main research lane, but its analysis launch is temporarily deferred while a Strata-inspired finite-memory side study is opened.

The side study must not silently modify LABEL-001.

## Next action

Let ordinary CI validate this fix while STRATA-001 Council/provenance work proceeds independently.

## Authority boundary

No provider or memory intervention is authorized.
