# STRATA-008 Cold-Capacity Invariance Design v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

If total one-shot cold data is doubled while pressure, hot live set, release cadence, runtime, and hosted image remain fixed, does the pressure-event knee and retained resident floor remain bounded?

The current leading mechanism is:

`K ~= MemoryHigh - effective_live_set`

If that mechanism is genuinely about instantaneous live state rather than total dataset capacity, then increasing a semantically one-shot cold stream should increase work and advice-call count but should not materially shift the knee or post-scan retained floor under DONTNEED.

## Parent evidence

STRATA-007 on Ubuntu 26.04 used:

- MemoryHigh 160 MiB
- hot anon 64 MiB
- cold file 96 MiB
- DONTNEED cadence panel 64 / 72 / 80 / 88 / 96 MiB

and observed:

`80 MiB < K <= 88 MiB`

`144 MiB < K+hot <= 152 MiB`

with DONTNEED non-hot post-scan floor median `12.8125 MiB`.

Reuse STRATA-007 as the 96 MiB anchor. Do not repeat it in v1.

## New causal axis

Change only total cold-file size:

`192 MiB`

This doubles the one-shot cold stream.

Hold constant:

- runner: `ubuntu-26.04`
- Python: 3.12
- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- hot anon: 64 MiB
- read chunk: 4 MiB
- file preparation semantics
- DONTNEED implementation
- Recorder density: 26 records/trial
- cgroup/systemd-run execution pattern

## Cadence panel

Use:

- buffered
- DONTNEED 64 MiB
- DONTNEED 72 MiB
- DONTNEED 80 MiB
- DONTNEED 88 MiB
- DONTNEED 96 MiB

## Trial budget

- one new cold-file size
- 6 arms
- 4 independent runner blocks
- 24 total new trials

The 96 MiB anchor remains historical evidence.

## Competing hypotheses

### H-bounded-working-set

Total cold capacity does not determine the knee.

Predictions:

- 192 MiB remains compatible with `80 < K <= 88 MiB`;
- `144 < K+hot <= 152 MiB`;
- DONTNEED post-scan non-hot floor remains compatible with the prior `[8,16) MiB` interval;
- advice calls increase where the larger stream crosses additional release boundaries.

### H-capacity-coupled

Doubling total cold bytes materially shifts the onset or retained floor even under the same release cadence.

That would mean total dataset capacity contributes to instantaneous memory demand in a way not captured by the current headroom model.

## Primary outcomes

- MemoryHigh event delta
- maximum scan memory.current
- post-scan memory.current
- post-scan file residency
- onset bracket
- transformed `K+hot`
- effective/non-hot floor intervals

## Capacity-specific outcomes

Also report:

- advice calls
- bytes scanned
- cold-file size
- scan elapsed time as descriptive only

The study must distinguish "more total work" from "more instantaneous resident memory."

## Environment receipt repair

STRATA-007 exposed an empty `systemd_version` field.

Future receipt must query:

`systemd-run --version | head -n1`

because `systemd-run` is the executable actually used by the harness.

Retain kernel, OS release, image version, architecture, and cgroup filesystem receipts.

## Pseudo-Council

- **Systems:** total stream size is the next distinct axis after pressure, hot live set, and image.
- **Finite-RAM mechanism:** a bounded streaming policy should decouple instantaneous resident demand from total one-shot capacity.
- **Statistics:** four blocks are sufficient for directional invariance screening, not universal proof.
- **Economics:** reuse the 96 MiB anchor and run only one doubled-capacity condition.
- **Recorder:** repair the concrete systemd receipt defect in the new workflow.
- **Authority:** design freeze does not grant launch or policy authority.

Consensus:

**freeze a 192 MiB cold-capacity screen against the existing 96 MiB Ubuntu 26.04 anchor.**

## Monte Carlo

Deferred.

The physical doubled-capacity observation is more informative than a synthetic model of scaling before measuring it.

## Launch boundary

This document freezes design only.
Implementation is a separate bounce.
Hosted launch requires a later explicit marker.
No local-PC execution is authorized.
