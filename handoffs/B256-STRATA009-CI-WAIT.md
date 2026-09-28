# Bounce Handoff

> **Bounce ID:** B256
> **Status:** EXTERNAL_WAIT / STRATA-009 IMPLEMENTATION CI QUEUED

## B255 implementation

Exact implementation commit:

`fe819f2fa9948c6fa63e741919f997e25f7daffa`

Implemented but not launched:

- 384 MiB cold-file spec
- bounded-policy-only scheduler/trial/aggregate
- Ubuntu 26.04 workflow
- 98-record Recorder contract
- regression tests

No `launch/STRATA-009-v1.txt` marker exists.

## CI

Exact-head ordinary CI:

`36438923685`

Single status read in B256:

`queued`

No second read was performed.

## Scientific state

STRATA-009 has not executed.

No dataset-over-MemoryMax scientific evidence exists yet.

## Next fresh-bounce action

Read CI run `36438923685` exactly once.

- success -> create explicit STRATA-009 launch marker in a separate bounce;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-009 launch.
No memory-control policy.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
