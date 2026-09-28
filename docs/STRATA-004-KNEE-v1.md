# STRATA-004-KNEE-v1

> **Status:** FROZEN TARGETED REFINEMENT CONTRACT
> **Purpose:** localize the DONTNEED pressure-avoidance transition inside the STRATA-003 bracket

## Parent evidence

STRATA-003-PILOT-v1 established:

`32 MiB < observed pressure-avoidance knee <= 96 MiB`

under the frozen hosted workload.

No OSS default cadence is authorized.

## Frozen workload

- runner: GitHub-hosted Ubuntu 24.04
- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- HOT anonymous guardrail: 64 MiB
- COLD file: 96 MiB
- buffered read chunk: 4 MiB
- scan-time checkpoint cadence: 4 MiB

Only release cadence changes.

## Arms

| Arm | DONTNEED cadence |
| --- | ---: |
| buffered | none |
| dontneed_32m | 32 MiB |
| dontneed_48m | 48 MiB |
| dontneed_64m | 64 MiB |
| dontneed_72m | 72 MiB |
| dontneed_80m | 80 MiB |
| dontneed_88m | 88 MiB |
| dontneed_96m | 96 MiB / end of stream |

All DONTNEED ranges must be page aligned.

The direct/O_DIRECT arm is intentionally omitted from this refinement because the question is the location of the buffered-DONTNEED transition, not re-establishing the already-observed direct reference.

## Design

- 8 independent runner blocks
- 8 arms
- one trial per arm per block
- 64 total trials
- deterministic shuffled arm order

## Primary outcomes

1. MemoryHigh event delta during scan
2. maximum observed scan-time memory.current
3. post-scan memory.current
4. post-scan file residency

## Secondary outcomes

- advice calls and calls/GiB
- scan elapsed / throughput
- pgscan / pgsteal
- HOT anonymous residency
- HOT retouch time
- swap / OOM
- post-scan cgroup file bytes

Hosted timing remains secondary and must not alone select a cadence.

## Environment provenance

Record once per runner block:

- kernel release
- OS release identity
- systemd version
- cgroup filesystem type / v2 presence

This metadata is provenance for later external-validity work. It does not turn one hosted substrate into a portability claim.

## Validity checks

Invalidate a trial if:

- pre-scan file residency > 10%
- DONTNEED call fails
- release range is not page aligned
- full 96 MiB span is not processed
- content integrity fails
- OOM occurs

The aggregate is invalid if:

- all 8 blocks are not present
- all 64 trials are not present
- each arm is not present exactly once per block
- any trial is INVALID

## Knee interpretation

If the response is monotone, report the narrowest adjacent tested interval where the lower cadence remains pressure-free and the upper cadence produces pressure.

If the response is not monotone across blocks or intervals, report NON_MONOTONE / AMBIGUOUS and retain all block-level evidence.

Do not collapse ambiguity to a single threshold.

## Model heuristic boundary

The ~82 MiB transition estimate derived from STRATA-003 4/8/16/32 MiB medians is a design heuristic only.

It is not a prior that may override observed STRATA-004 evidence.

## Monte Carlo disposition

Not part of STRATA-004-KNEE-v1.

Monte Carlo remains a later candidate for adaptive headroom-policy robustness after the empirical response surface is localized.

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default cadence selection.
Proposal != Decision.
Expressibility != Executability.
