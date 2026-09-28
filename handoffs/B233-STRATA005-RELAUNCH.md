# Bounce Handoff

> **Bounce ID:** B233
> **Status:** STRATA-005 EXPLICIT HOSTED RELAUNCH

## Rehydration

Canonical predecessor: B232.

B232 required exactly one read of repair CI run `36430872975`.

## Repair CI

The run was read once in B233:

- run: `36430872975`
- head: `baf6264a4bdee456e040ab1015b2eb7f7f059cc1`
- status: completed
- conclusion: success

No second read was performed.

## Relaunch decision

The predecessor scientific run `36430416271` is not rerun.

It produced zero valid scientific trials and failed only because the systemd-run child received a repository-relative spec path.

A new explicit marker revision is created in this bounce:

`launch/STRATA-005-v1.txt`

The new execution remains bound to the frozen STRATA-005 design.

## Frozen study

- MemoryHigh: 144 / 176 MiB
- arms: buffered / DONTNEED 48 / 64 / 80 / 96 MiB
- blocks: 4 per pressure
- total trials: 40
- REC-001 records: 26 per trial

## Monte Carlo

Still deferred. No valid cross-pressure observations exist yet.

## Next action

Discover the STRATA-005 workflow run for this exact relaunch commit once.

- success -> fetch artifacts once, validate the 40-trial matrix, atomize results, and run pseudo-Council;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant; no blind retry.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
