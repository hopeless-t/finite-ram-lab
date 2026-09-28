# CURRENT

> **Latest bounce:** B247
> **Stage:** STRATA-007 PASS / CROSS-IMAGE PORTABILITY SUPPORTED
> **Turn stop reason:** READY_FOR_NEXT_DESIGN

## Canonical cross-image result

STRATA-007 run:

`36435758885`

Launch SHA:

`615cc9957d4f7e49cc60a7d799431ba149d6f22b`

Aggregate:

- artifact `STRATA-007-CROSS-IMAGE-36435758885`
- id `10975842099`
- digest `sha256:1f677697ec810dd1f25dee0c7657044d55a52dee3874806579266bbae2370eb4`
- trials 24 / 24
- PASS

Ubuntu 26.04 result:

`80 < K <= 88 MiB`

`144 < K+hot <= 152 MiB`

Ubuntu 24.04 STRATA-004 anchor has the same brackets.

All four 26.04 blocks reproduced the same onset.

## Leading mechanism

Across pressure, live-set, and hosted-image axes:

`K ~= MemoryHigh - effective_live_set`

remains the leading tested mechanism.

The non-hot component is measurable but not universal.

Ubuntu 26.04 DONTNEED non-hot floor:

- median 12.8125 MiB
- range approximately 12.805–13.313 MiB

## Recorder sidecar issue

The STRATA-007 environment receipt captured a blank `systemd_version` field.

The scientific run remains valid because `systemd-run` executed successfully and the new image/kernel identity was recorded.

Future receipts must query `systemd-run --version` rather than `systemd --version`.

## Monte Carlo

Deferred. Two substrate families with identical coarse onset intervals do not identify a useful portability distribution.

## Next fresh-bounce action

Freeze a total-cold-volume test:

- runner Ubuntu 26.04
- MemoryHigh 160 MiB
- hot anon 64 MiB
- current 96 MiB cold-file result reused as anchor
- increase total cold file size materially
- preserve read chunk, DONTNEED mechanism, cadence panel, Recorder density
- ask whether knee and retained floor remain bounded independently of total cold capacity

Do not launch in the design bounce.

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
