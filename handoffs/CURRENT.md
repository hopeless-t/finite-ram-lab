# CURRENT

> **Latest bounce:** B238
> **Stage:** STRATA-006 IMPLEMENTED + CI MATERIALIZATION WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Canonical parent result

STRATA-005 run `36431449193`: PASS, 40/40.

Directional result:

`K = MemoryHigh - effective_live_set_floor`

is more consistent with the tested data than a universal fixed raw-MiB knee.

No controller/default is authorized.

## STRATA-006 implementation

Exact B237 commit:

`65035dfc4d4e2f9e5ec4075dda84fc39807e69cc`

Frozen test:

- MemoryHigh 160 MiB
- hot anon 56 / 72 MiB
- reuse hot=64 MiB STRATA-004 anchor
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks per hot
- 48 total new trials
- REC-001 density unchanged

Primary discriminator:

`K + hot_anon ~= constant`

versus fixed raw `K`.

Implementation exists but launch has not occurred.

## CI discovery

One exact-head discovery read in B238:

`0 matching workflow runs`

Do not infer failure and do not create a launch marker yet.

## Monte Carlo

Deferred until STRATA-006 physical observations exist.

## Next fresh-bounce action

Search exact head `65035dfc4d4e2f9e5ec4075dda84fc39807e69cc` for ordinary CI once.

- success -> explicit STRATA-006 launch in a new bounce;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only;
- absent -> EXTERNAL_WAIT without retry.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state
- LLM-jp-4.1 local worker + state-lifetime dogfood

These remain proposals only.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-006 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
