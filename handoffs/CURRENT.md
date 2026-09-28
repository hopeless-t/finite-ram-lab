# CURRENT

> **Latest bounce:** B240
> **Stage:** STRATA-006 / HOSTED RUN LAUNCHED + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Canonical parent result

STRATA-005 run `36431449193`: PASS, 40/40.

Directional model under test:

`K = MemoryHigh - effective_live_set_floor`

## STRATA-006 frozen contract

- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- hot anon: 56 / 72 MiB
- existing hot=64 MiB STRATA-004 anchor retained separately
- arms: buffered / DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks per hot setting
- 48 total new trials
- REC-001: 26 records/trial

Primary discriminator:

`K + hot_anon ~= constant`

versus fixed raw `K`.

## Launch

Exact launch commit:

`f9fc73fcf8170b129f2e1a91e1f8614d3927ed8e`

Hosted STRATA-006 run:

`36434232753`

Single discovery/status read in B240:

`queued`

Do not poll again in this bounce.

Ordinary CI `36434232954` also exists and was queued at discovery; it is not the scientific result and was not polled.

## Monte Carlo

Deferred until valid live-set-axis observations exist.

## Next fresh-bounce action

Read run `36434232753` exactly once.

- success -> fetch aggregate artifact once and validate/atomize all 48 trials;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant; no blind rerun.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state
- LLM-jp-4.1 local worker + state-lifetime dogfood

These remain proposals only.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
