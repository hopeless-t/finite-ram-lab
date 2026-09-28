# CURRENT

> **Latest bounce:** B246
> **Stage:** STRATA-007 / LAUNCH COMMITTED + RUN MATERIALIZATION WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Canonical mechanism

Ubuntu 24.04 evidence currently supports:

`K ~= MemoryHigh - effective_live_set`

At MemoryHigh 160 MiB, hot anon 64 MiB:

`80 < K <= 88 MiB`

and:

`144 < K+hot <= 152 MiB`.

## STRATA-007 launch

Exact B245 launch commit:

`615cc9957d4f7e49cc60a7d799431ba149d6f22b`

Explicit marker:

`launch/STRATA-007-v1.txt`

Frozen execution:

- runner `ubuntu-26.04`
- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 96 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 trials
- REC-001 density unchanged

Ubuntu 24.04 is reused only as historical anchor.

## Run discovery

One exact-head discovery read was performed after B245.

Result:

`0 matching workflow runs`

Interpretation: run materialization/delivery is not yet known.

Do not infer failure and do not launch again.

## Monte Carlo

Deferred until cross-image physical observations exist.

## Next fresh-bounce action

Search exact head `615cc9957d4f7e49cc60a7d799431ba149d6f22b` for push-triggered runs once.

- STRATA-007 success -> fetch aggregate artifact once and validate/atomize 24 trials;
- pending/in_progress -> checkpoint EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant;
- absent -> EXTERNAL_WAIT without retry.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state
- LLM-jp-4.1 local worker + state-lifetime dogfood

No local execution is authorized.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
