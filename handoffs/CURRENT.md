# CURRENT

> **Latest bounce:** B241
> **Stage:** STRATA-006 PASS / LIVE-SET HEADROOM MECHANISM REPLICATED
> **Turn stop reason:** READY_FOR_NEXT_DESIGN

## STRATA-006 canonical PASS

Run:

`36434232753`

Launch SHA:

`f9fc73fcf8170b129f2e1a91e1f8614d3927ed8e`

Aggregate artifact:

- name: `STRATA-006-LIVESET-HEADROOM-36434232753`
- id: `10974842004`
- digest: `sha256:4bee6f7e6cd1b0efdc342187d08204513f2f3e05e7422ad8a87c5d05353e6eb7`
- trials: 48 / 48
- execution status: PASS

## Mechanism result

At MemoryHigh=160 MiB:

- hot=56: `88 < K <= 96`
- hot=64 STRATA-004 anchor: `80 < K <= 88`
- hot=72: `72 < K <= 80`

Each transforms to:

`144 < K + hot <= 152 MiB`

Block replication:

- hot=56: 4/4 blocks same bracket
- hot=72: 4/4 blocks same bracket

Measured DONTNEED non-hot floor:

- hot=56 median: 12.734375 MiB
- hot=72 median: 12.794921875 MiB

Leading tested mechanism on this hosted substrate:

`K ~= MemoryHigh - effective_live_set`

with:

`effective_live_set ~= hot_anon + substrate/workload overhead`

The observed ~12.8 MiB non-hot floor is not a portable constant or OSS default.

Full result:

`docs/STRATA-006-RESULT.md`

## Monte Carlo

Deferred. Cross-substrate variation has not yet been measured.

## Next fresh-bounce action

Freeze a portability design that changes hosted software substrate/image while preserving:

- MemoryHigh
- hot anon
- cold file
- read chunk
- DONTNEED implementation
- cadence panel
- Recorder density

Prefer one new substrate against a reusable current-substrate anchor.

Do not launch in the design bounce.

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
