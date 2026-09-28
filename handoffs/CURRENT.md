# CURRENT

> **Latest bounce:** B232
> **Stage:** STRATA-005 / SPEC-PATH REPAIR + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Failed hosted study attempt

Run `36430416271` completed with failure before scientific measurement.

- 8 / 8 matrix jobs failed at spec loading
- valid STRATA-005 trials: 0
- aggregate skipped
- no pressure/DONTNEED inference authorized

Root cause:

`systemd-run` child received repository-relative `specs/STRATA-005-EXTERNAL-VALIDITY-v1.json`.

## Repair

B231 commit:

`baf6264a4bdee456e040ab1015b2eb7f7f059cc1`

The trial now receives:

`$GITHUB_WORKSPACE/specs/STRATA-005-EXTERNAL-VALIDITY-v1.json`

through an explicit absolute-path variable. A regression test guards the workflow contract.

Frozen design remains unchanged:

- MemoryHigh: 144 / 176 MiB
- arms: buffered / DONTNEED 48 / 64 / 80 / 96 MiB
- 4 blocks per pressure
- 40 total trials
- 26 REC-001 records per trial

## CI

Exact-head CI run:

`36430872975`

Single B232 read:

`queued`

Do not poll again in this bounce.

## Source intake

Naive-N0.5-Flash remains recorded as mechanism/measurement-design input for a later semantic-reuse study. It does not alter STRATA-005.

## Monte Carlo

Deferred until valid cross-pressure observations exist.

## Next fresh-bounce action

Read `36430872975` exactly once.

- success -> make a new explicit STRATA-005 relaunch marker change;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant.

Do not use rerun on `36430416271`.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
