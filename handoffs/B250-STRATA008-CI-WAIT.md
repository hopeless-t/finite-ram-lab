# Bounce Handoff

> **Bounce ID:** B250
> **Status:** EXTERNAL_WAIT / STRATA-008 IMPLEMENTATION CI IN PROGRESS

## B249 implementation

Exact implementation commit:

`d709e9e7c71b03faa9e519079c42663f3feb3a8e`

Implemented but not launched:

- 192 MiB cold-capacity spec
- deterministic scheduler/trial/aggregate
- Ubuntu 26.04 hosted workflow
- repaired systemd receipt using `systemd-run --version`
- regression tests

No `launch/STRATA-008-v1.txt` marker exists.

## CI

Exact-head ordinary CI:

`36436853395`

Single status read in B250:

`in_progress`

No second read was performed.

## Scientific state

STRATA-008 has not executed.

No doubled-capacity scientific evidence exists yet.

Monte Carlo remains deferred.

## Next fresh-bounce action

Read CI run `36436853395` exactly once.

- success -> create explicit STRATA-008 launch marker in a separate bounce;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-008 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
