# CURRENT

> **Latest bounce:** B245
> **Stage:** STRATA-007 / EXPLICIT HOSTED LAUNCH
> **Turn stop reason:** RUN_DISCOVERY_PENDING

## Canonical mechanism

STRATA-006 on Ubuntu 24.04 supports:

`K ~= MemoryHigh - effective_live_set`

with transformed interval:

`144 < K+hot <= 152 MiB`.

## STRATA-007 validation

Implementation commit:

`a1e3f4ab042d3272178c6f435b88f2d25a8c01de`

Ordinary CI:

`36435391877`

Single B245 read:

- completed
- success

## Launch

B245 creates:

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
- 24 total new trials
- REC-001 density unchanged

Ubuntu 24.04 remains historical anchor only.

## Monte Carlo

Deferred until cross-image observations exist.

## Next fresh-bounce action

Discover/read the STRATA-007 workflow run for the exact B245 launch commit once.

- success -> fetch aggregate artifact once and validate/atomize 24 trials;
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
