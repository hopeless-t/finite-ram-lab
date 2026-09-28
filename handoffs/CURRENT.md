# CURRENT

> **Latest bounce:** B225
> **Stage:** STRATA-005 IMPLEMENTED / CI VALIDATION NEXT / NOT LAUNCHED

## Canonical parent evidence

REC-002 run `36427808785` passed 16/16 trials and found zero MemoryHigh-event regime changes across all 8 paired blocks. Recorder is accepted for STRATA-005 only at the tested density.

## STRATA-005 implementation

Frozen design:
- MemoryHigh 144 and 176 MiB
- buffered + DONTNEED 48/64/80/96 MiB
- 4 blocks per pressure
- 40 hosted trials
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 96 MiB

B225 added the machine-readable spec, deterministic scheduler/aggregator, unit tests, and a hosted workflow.

The workflow is `workflow_dispatch` only. This commit does not launch STRATA-005.

## Pseudo-Council

Converged: vary one causal axis only. Do not add runner-substrate variation until cross-pressure evidence exists. Keep throughput descriptive. Do not infer a controller formula from two pressure settings.

## Monte Carlo

Deferred until empirical cross-pressure observations exist.

## Next action

Read ordinary CI for the B225 exact head once.

- success -> launch STRATA-005 in a separate explicit bounce;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> inspect only the exposed implementation failure and repair atomically.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
