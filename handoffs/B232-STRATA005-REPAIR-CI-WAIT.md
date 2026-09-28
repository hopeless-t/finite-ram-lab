# Bounce Handoff

> **Bounce ID:** B232
> **Status:** EXTERNAL_WAIT / STRATA-005 SPEC-PATH REPAIR CI QUEUED

## B231 repair

Exact repair commit:

`baf6264a4bdee456e040ab1015b2eb7f7f059cc1`

The exposed STRATA-005 failure was a portable-path defect at the systemd-run boundary:

- failed scientific run: `36430416271`
- valid scientific trials from that run: 0
- root cause: relative spec path not resolvable inside the transient unit
- repair: pass spec through `$GITHUB_WORKSPACE` absolute path
- regression test added for the workflow contract

No frozen experiment parameter changed.

## CI

Exact-head ordinary CI:

`36430872975`

Single discovery/status read in this bounce:

`queued`

No second read was performed.

## Next fresh-bounce action

Read CI run `36430872975` exactly once.

- success -> create a distinct explicit STRATA-005 relaunch marker change; do not rerun the failed run;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the newly exposed invariant.

## Scientific state

There are still no valid STRATA-005 cross-pressure observations.

Monte Carlo remains deferred.

## Authority boundary

Hosted research/repository work only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
