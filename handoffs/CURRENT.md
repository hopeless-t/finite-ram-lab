# CURRENT

> **Latest bounce:** B250
> **Stage:** STRATA-008 IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Canonical mechanism

STRATA-007 established cross-image agreement at current resolution:

- Ubuntu 24.04 anchor: `80 < K <= 88 MiB`
- Ubuntu 26.04: `80 < K <= 88 MiB`

Both map to:

`144 < K+hot <= 152 MiB`.

Leading tested mechanism:

`K ~= MemoryHigh - effective_live_set`

## STRATA-008 implementation

Exact B249 commit:

`d709e9e7c71b03faa9e519079c42663f3feb3a8e`

Frozen doubled-capacity test:

- Ubuntu 26.04
- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 192 MiB
- read chunk 4 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 trials

96 MiB cold-file STRATA-007 is reused as historical anchor.

Recorder records/trial = 50 because the 192 MiB stream creates 48 four-MiB scan checkpoints plus start/end.

Environment receipt uses `systemd-run --version`.

No launch marker exists.

## CI

Exact-head CI:

`36436853395`

Single B250 read:

`in_progress`

Do not poll again in this bounce.

## Monte Carlo

Deferred until doubled-capacity physical evidence exists.

## Next fresh-bounce action

Read `36436853395` exactly once.

- success -> explicit STRATA-008 launch in a separate commit;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state
- LLM-jp-4.1 local worker + state-lifetime dogfood

No local execution is authorized.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-008 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
