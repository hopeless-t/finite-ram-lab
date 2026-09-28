# CURRENT

> **Latest bounce:** B239
> **Stage:** STRATA-006 / EXPLICIT HOSTED LAUNCH
> **Turn stop reason:** RUN_DISCOVERY_PENDING

## Canonical parent result

STRATA-005 run `36431449193`: PASS, 40/40.

Current directional interpretation:

`K = MemoryHigh - effective_live_set_floor`

is more consistent with tested data than a universal fixed raw-MiB knee.

## STRATA-006 validation

Implementation commit:

`65035dfc4d4e2f9e5ec4075dda84fc39807e69cc`

Ordinary CI:

`36433776719`

Single B239 read:

- completed
- success

## Launch

B239 creates:

`launch/STRATA-006-v1.txt`

Frozen execution contract:

- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 56 / 72 MiB
- reuse hot=64 MiB STRATA-004 anchor
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks per hot setting
- 48 total new trials
- REC-001 density unchanged

Primary discriminator:

`K + hot_anon ~= constant`

versus fixed raw `K`.

## Monte Carlo

Deferred until valid STRATA-006 observations exist.

## Next fresh-bounce action

Discover/read the STRATA-006 workflow run for the exact B239 launch commit once.

- success -> fetch artifact once and validate/atomize 48 trials;
- pending/in_progress -> checkpoint EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant;
- absent -> EXTERNAL_WAIT without retry.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state
- LLM-jp-4.1 local worker + state-lifetime dogfood

No local execution is authorized for either.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
