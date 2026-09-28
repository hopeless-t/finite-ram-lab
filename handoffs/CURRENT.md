# CURRENT

> **Latest bounce:** B242
> **Stage:** STRATA-007 CROSS-IMAGE PORTABILITY DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## Canonical mechanism

STRATA-005/006 support on GitHub-hosted Ubuntu 24.04:

`K ~= MemoryHigh - effective_live_set`

with direct live-set replication at MemoryHigh=160 MiB.

STRATA-006 full result:

`docs/STRATA-006-RESULT.md`

## STRATA-007 frozen design

New hosted image:

`ubuntu-26.04`

Reuse Ubuntu 24.04 STRATA-004 as anchor.

Freeze:

- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 96 MiB
- read chunk 4 MiB
- Python 3.12 requested explicitly
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 new trials
- REC-001 density unchanged

Portability discriminator:

- prior 24.04: `80 < K <= 88`
- transformed: `144 < K+hot <= 152`

If 26.04 shifts outside the compatible interval, introduce an explicit substrate-overhead term rather than forcing one universal constant.

Design:

`docs/STRATA-007-CROSS-IMAGE-v1.md`

## Monte Carlo

Deferred until cross-image observations exist.

## Next fresh-bounce action

Implement STRATA-007:

- spec
- deterministic schedule / trial / aggregate
- `ubuntu-26.04` hosted workflow
- environment receipt
- tests

Do not launch during implementation.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state
- LLM-jp-4.1 local worker + state-lifetime dogfood

These remain proposals only.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-007 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
