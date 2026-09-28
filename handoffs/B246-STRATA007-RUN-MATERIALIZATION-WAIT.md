# Bounce Handoff

> **Bounce ID:** B246
> **Status:** EXTERNAL_WAIT / STRATA-007 RUN MATERIALIZATION

## Launch

Exact B245 launch commit:

`615cc9957d4f7e49cc60a7d799431ba149d6f22b`

Explicit marker:

`launch/STRATA-007-v1.txt`

Main ref update returned success.

## External run discovery

A single exact-head push-run discovery was performed for B245.

Result at that read:

- matching workflow runs: 0
- STRATA-007 run ID: not yet materialized

This is an unknown materialization state, not evidence that launch failed.

No second discovery query was performed.

## Retry policy

Do not:

- touch the launch marker again in this bounce;
- dispatch the workflow manually;
- infer a new execution grant from the absent run record;
- duplicate the Ubuntu 24.04 anchor.

## Scientific state

No STRATA-007 cross-image evidence exists yet.

Frozen comparison remains:

- new image: Ubuntu 26.04
- historical anchor: Ubuntu 24.04 STRATA-004
- MemoryHigh 160 MiB
- hot anon 64 MiB
- expected prior interval: `80 < K <= 88 MiB`
- transformed prior interval: `144 < K+hot <= 152 MiB`

Monte Carlo remains deferred.

## Next fresh-bounce action

Search exact head `615cc9957d4f7e49cc60a7d799431ba149d6f22b` for push-triggered runs once.

- STRATA-007 success -> fetch aggregate artifact once and analyze 24 trials;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant;
- still absent -> checkpoint EXTERNAL_WAIT again without launching another execution.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
