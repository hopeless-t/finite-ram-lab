# CURRENT

> **Latest bounce:** B234
> **Stage:** STRATA-005 / RELAUNCH COMMITTED + RUN MATERIALIZATION WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Repair validation

Spec-path repair:

`baf6264a4bdee456e040ab1015b2eb7f7f059cc1`

CI `36430872975`: completed / success.

## Prior failed run

Run `36430416271` remains invalid for scientific inference:

- valid trials: 0
- failure occurred before scientific measurement
- no blind rerun

## Relaunch

Exact B233 commit:

`9f0ed686406a49b42e14d855e3d941970e55c94d`

The commit revised `launch/STRATA-005-v1.txt` as a new explicit execution after validated repair.

Main ref update returned success.

## Run discovery

One exact-head discovery read was performed immediately after B233.

Result:

`0 matching workflow runs`

Interpretation: run materialization/delivery is not yet known. Do not infer failure and do not launch again.

## Frozen STRATA-005 contract

- MemoryHigh: 144 / 176 MiB
- arms: buffered / DONTNEED 48 / 64 / 80 / 96 MiB
- 4 blocks per pressure
- 40 total trials
- 26 REC-001 records per trial

## Monte Carlo

Deferred until valid cross-pressure observations exist.

## Next fresh-bounce action

Search exact head `9f0ed686406a49b42e14d855e3d941970e55c94d` for push-triggered runs once.

- STRATA-005 success -> fetch artifacts once and validate/atomize 40 trials;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect the exposed invariant only;
- absent -> checkpoint EXTERNAL_WAIT; do not relaunch.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
