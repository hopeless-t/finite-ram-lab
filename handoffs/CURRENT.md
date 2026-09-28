# CURRENT

> **Latest bounce:** B233
> **Stage:** STRATA-005 / EXPLICIT HOSTED RELAUNCH
> **Turn stop reason:** RUN_DISCOVERY_PENDING

## Repair validation

Spec-path repair commit:

`baf6264a4bdee456e040ab1015b2eb7f7f059cc1`

Ordinary CI run `36430872975` was read exactly once in B233:

- status: completed
- conclusion: success

## Prior failed run

`36430416271` remains invalid for scientific inference:

- failed before spec loading completed
- valid trials: 0
- no DONTNEED/headroom result
- do not rerun it

## STRATA-005 frozen contract

- MemoryHigh: 144 / 176 MiB
- arms: buffered / DONTNEED 48 / 64 / 80 / 96 MiB
- 4 blocks per pressure
- 40 total trials
- 26 REC-001 records per trial

## Relaunch

B233 revises the explicit path-gated marker:

`launch/STRATA-005-v1.txt`

This is a new explicit hosted execution after validated repair. It does not change the study design.

## Source intake

Naive-N0.5-Flash remains recorded as mechanism/measurement-design input for a later semantic-reuse study only.

## Monte Carlo

Deferred until valid cross-pressure observations exist.

## Next fresh-bounce action

Discover/read the STRATA-005 run for the exact B233 relaunch commit once.

- success -> fetch artifacts once and validate/atomize all 40 trials;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
