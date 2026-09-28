# Bounce Handoff

> **Bounce ID:** B235
> **Status:** COMPLETE / STRATA-005 PASS / HEADROOM MECHANISM SUPPORTED

## Rehydration

Canonical predecessor: B234.

B234 required one exact-head run discovery for B233 relaunch commit `9f0ed686406a49b42e14d855e3d941970e55c94d`.

## Hosted result

Run `36431449193` materialized and completed successfully.

Aggregate artifact:

- name: `STRATA-005-EXTERNAL-VALIDITY-36431449193`
- id: `10973632531`
- digest: `sha256:8702206b4cb645796f0c2ca17f60bc155898d380225f6216804b790396592554`
- execution status: PASS
- trials: 40 / 40

## Scientific result

Onset brackets:

- MemoryHigh 144 MiB: `64 < knee <= 80 MiB`
- MemoryHigh 160 MiB anchor: `80 < knee <= 88 MiB`
- MemoryHigh 176 MiB: `knee > 96 MiB`

A universal fixed raw-MiB knee has empty interval intersection.

For `K = H - B`, the three observations admit a common:

`B in [72, 80) MiB`

Measured STRATA-005 DONTNEED post-scan resident floor median:

`~76.72 MiB`

Council therefore accepts directional support for effective-live-set headroom and does not authorize a fixed cadence, controller formula, or OSS default.

## Monte Carlo

Deferred because the deterministic interval evidence already separates the hypotheses and the available aggregate brackets do not identify a defensible jitter distribution.

## Next action

Freeze a hosted study that varies hot/live resident set while holding MemoryHigh constant.

The high-information question is whether the release-cadence knee shifts inversely with live-set size.

Naive-N0.5-Flash semantic reuse and LLM-jp local-worker dogfood remain queued future studies; neither should displace this direct mechanism test.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
