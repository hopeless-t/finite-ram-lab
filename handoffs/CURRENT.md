# CURRENT

> **Latest bounce:** B244
> **Stage:** STRATA-007 IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Canonical mechanism

STRATA-006 run `36434232753`: PASS, 48/48.

Leading tested mechanism on Ubuntu 24.04:

`K ~= MemoryHigh - effective_live_set`

with hot-set replication:

- hot56 -> `88 < K <= 96`
- hot64 -> `80 < K <= 88`
- hot72 -> `72 < K <= 80`

all mapping to:

`144 < K+hot <= 152 MiB`.

## STRATA-007 implementation

Exact B243 commit:

`a1e3f4ab042d3272178c6f435b88f2d25a8c01de`

Frozen portability screen:

- new runner `ubuntu-26.04`
- existing `ubuntu-24.04` STRATA-004 anchor
- explicit Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 96 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 trials
- REC-001 density unchanged

No launch marker exists.

## CI

Exact-head CI run:

`36435391877`

Single B244 read:

`in_progress`

Do not poll again in this bounce.

## Monte Carlo

Deferred until cross-image observations exist.

## Next fresh-bounce action

Read `36435391877` exactly once.

- success -> explicit STRATA-007 launch in a separate commit;
- pending/in_progress -> checkpoint EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state
- LLM-jp-4.1 local worker + state-lifetime dogfood

No local execution is authorized.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-007 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
