# CURRENT

> **Latest bounce:** B231
> **Stage:** STRATA-005 / PORTABLE SPEC-PATH REPAIR / CI PENDING

## Failed hosted run

Run `36430416271`:

- completed / failure
- 8 / 8 matrix jobs failed before scientific measurement
- valid STRATA-005 trials: 0
- aggregate skipped

Representative root cause:

`FileNotFoundError: specs/STRATA-005-EXTERNAL-VALIDITY-v1.json`

This run carries no pressure or DONTNEED inference.

## B231 repair

The `systemd-run` trial boundary no longer depends on repository cwd.

The workflow now passes the spec using:

`$GITHUB_WORKSPACE/specs/STRATA-005-EXTERNAL-VALIDITY-v1.json`

A workflow-contract regression test rejects restoration of the relative trial spec path.

Frozen STRATA-005 design is unchanged:

- MemoryHigh: 144 / 176 MiB
- arms: buffered / DONTNEED 48 / 64 / 80 / 96 MiB
- 4 blocks per pressure
- 40 trials
- 26 REC-001 records per trial

## Source intake

Naive-N0.5-Flash remains a later-study mechanism and measurement-design source only. It does not modify STRATA-005.

## Monte Carlo

Deferred: cross-pressure observations still do not exist.

## Next fresh-bounce action

Read B231 ordinary CI exactly once.

- success -> create a new explicit STRATA-005 relaunch marker change;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant.

Do not use GitHub's rerun action for `36430416271`; successful validation would authorize a new explicit launch, not a blind retry.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
