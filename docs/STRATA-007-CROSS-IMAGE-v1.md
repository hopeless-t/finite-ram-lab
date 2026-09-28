# STRATA-007 Cross-Image Portability Design v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY
> **Date:** 2026-09-28

## Question

Does the live-set headroom relation observed on GitHub-hosted Ubuntu 24.04 survive a materially different hosted Linux image when the workload and pressure variables are frozen?

Leading mechanism from STRATA-005/006:

`K ~= MemoryHigh - effective_live_set`

At MemoryHigh=160 MiB and hot anon=64 MiB, STRATA-004 established:

`80 MiB < K <= 88 MiB`

equivalently:

`144 MiB < K + hot <= 152 MiB`

and an effective-floor interval:

`72 MiB <= effective_live_set < 80 MiB`.

STRATA-007 asks whether that transformed relation survives an image/kernel/systemd change.

## New substrate

New hosted image:

`ubuntu-26.04`

Official runner-image state observed on 2026-09-28:

- Ubuntu 26.04.1 LTS
- kernel 7.0.0-1012-azure
- systemd 259.5-0ubuntu3.4
- image family available as `ubuntu-26.04`

Reference:

https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2604-Readme.md

Current anchor image family:

`ubuntu-24.04`

with the already-collected STRATA-004 evidence.

Reference:

https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md

Do not repeat 24.04 in v1. Reuse the frozen STRATA-004 anchor to reduce hosted cost.

## Frozen workload

Hold constant:

- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- hot anon: 64 MiB
- cold file: 96 MiB
- read chunk: 4 MiB
- file preparation semantics
- DONTNEED implementation
- Recorder density: 26 records/trial
- Python execution version requested by workflow: 3.12
- cgroup/systemd-run execution pattern

## Cadence panel

Use the common high-information panel:

- buffered
- DONTNEED 64 MiB
- DONTNEED 72 MiB
- DONTNEED 80 MiB
- DONTNEED 88 MiB
- DONTNEED 96 MiB

This includes the existing 24.04 onset bracket and enough lower/upper points to identify directional movement.

## Trial budget

- one new image
- 6 arms
- 4 independent runner blocks
- 24 total new trials

The prior Ubuntu 24.04 anchor is separate historical evidence and is not silently counted as new execution.

## Competing outcomes

### Portable transformed mechanism

The 26.04 onset remains compatible with:

`144 MiB < K + hot <= 152 MiB`

which at hot=64 means:

`80 MiB < K <= 88 MiB`.

The measured non-hot retained floor should also remain roughly compatible with the prior 8–16 MiB interval.

### Image-sensitive offset

The raw and transformed onset shifts materially, or the retained non-hot floor exits the prior interval.

That would indicate the model needs an explicit substrate term:

`K ~= MemoryHigh - hot - substrate_overhead`

rather than treating the overhead as stable.

## Primary outcomes

- MemoryHigh event delta during scan
- onset bracket
- maximum scan memory.current
- post-scan memory.current
- post-scan file residency
- `K + hot` interval
- effective floor interval
- non-hot floor interval

## Environment receipt

Each block must record:

- `uname -r`
- `systemd --version`
- cgroup filesystem type
- `/etc/os-release`
- GitHub runner image environment variables when available

The substrate receipt is evidence, not execution authority.

## Secondary outcomes

Retain:

- advice call count
- pgscan / pgsteal
- hot retouch cost
- scan elapsed time

Timing remains descriptive only.

## Pseudo-Council

- **Systems:** change the runner image only after pressure and live-set axes have both supported the same mechanism.
- **Causal inference:** keep Python at 3.12 and all workload parameters frozen to reduce avoidable confounding.
- **Portability:** prefer Ubuntu 26.04 over deprecated 22.04 for a forward-looking OSS portability screen.
- **Statistics:** four blocks are directional external validity, not universal portability proof.
- **Economics:** reuse the 24.04 anchor rather than paying for a duplicate control run.
- **Authority:** design freeze grants no implementation, launch, policy, or local-execution authority.

Consensus:

**freeze one new Ubuntu 26.04 image screen against the existing Ubuntu 24.04 anchor.**

## Monte Carlo

Deferred.

Cross-image physical evidence is more informative than assigning a synthetic substrate-offset distribution before measuring one.

## Launch boundary

This document freezes design only.
Implementation is a separate bounce.
Hosted launch requires a later explicit marker.
No local-PC execution is authorized.
