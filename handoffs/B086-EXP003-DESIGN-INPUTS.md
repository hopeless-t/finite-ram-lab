# Bounce Handoff

> **Bounce ID:** B086
> **Status:** COMPLETE / EXP-003 DESIGN-MC INPUTS SNAPSHOTTED

## Objective

Persist the minimum empirical inputs needed for the EXP-003 design Monte Carlo so Actions artifacts are not the sole durable source.

## Inputs

HYP-003:

- source run: 36247200797
- aggregate artifact: 10907254611
- compact rows: 32 runner-block × pressure strata
- fields: aligned/misaligned log-latency moments and HOT-residency means

EXP-002:

- source run: 36228994342
- aggregate artifact: 10902410851
- compact rows: 60 runner-block × arm strata
- fields: PAGEOUT call-cost, HOT-latency, total-interval, and residency moments

## Canonical files

- analysis/inputs/EXP-003-DESIGN-HYP003-block-strata.csv
- analysis/inputs/EXP-003-DESIGN-EXP002-block-arms.csv
- analysis/inputs/EXP-003-DESIGN-input-provenance.json

## Boundary

These are derived design inputs, not new experimental evidence.

## Next action

Implement only the EXP-003 design Monte Carlo over D1-D5 and frozen 0/25/50/75% capture scenarios, then checkpoint before launch.
