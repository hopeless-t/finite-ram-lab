# STRATA-006 Live-Set Headroom Design v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

If MemoryHigh is held constant while the hot/live resident set changes, does the DONTNEED pressure-event knee move inversely with live-set size?

STRATA-005 supported an additive headroom interpretation:

`K = H - B`

with a common effective live-set/reserve interval:

`B in [72, 80) MiB`

for H=144/160/176 under the existing 64 MiB hot-anon workload.

STRATA-006 tests the mechanism directly rather than adding another MemoryHigh setting.

## Causal axis

Hold constant:

- runner family: GitHub-hosted Ubuntu 24.04
- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- cold file: 96 MiB
- read chunk: 4 MiB
- cold-file preparation
- integrity checks
- DONTNEED implementation
- Recorder density: 26 records/trial

Vary only hot anonymous allocation:

- 56 MiB
- 72 MiB

Reuse the existing STRATA-004 64 MiB hot-anon result as the center anchor. Do not spend hosted budget repeating it in v1.

## Cadence panel

Use:

- buffered
- DONTNEED 64 MiB
- DONTNEED 72 MiB
- DONTNEED 80 MiB
- DONTNEED 88 MiB
- DONTNEED 96 MiB

The panel is intentionally concentrated around the existing 160 MiB knee.

## Trial budget

- 2 new hot-anon settings
- 6 arms
- 4 independent runner blocks per setting
- 48 total new trials

The 64 MiB hot-anon anchor remains the prior STRATA-004 64-trial study and is not silently pooled as new execution.

## Competing hypotheses

### H-fixed-raw

A universal raw cadence knee remains near the STRATA-004 bracket:

`80 MiB < K <= 88 MiB`

regardless of hot/live-set size.

### H-additive-live-set

If non-hot overhead remains approximately stable, then increasing hot anon by 8 MiB should reduce the knee by approximately 8 MiB, and decreasing hot anon by 8 MiB should increase it by approximately 8 MiB.

Equivalent transformed coordinate:

`K + hot_anon ~= constant`

STRATA-004 anchor implies:

`144 MiB < K + hot_anon <= 152 MiB`

This is a directional screen, not a fitted controller formula.

## Expected discriminating regions

These are predictions, not acceptance criteria.

Under the additive interpretation:

- hot=56 MiB -> knee should move toward the 88–96 MiB region;
- hot=72 MiB -> knee should move toward the 72–80 MiB region.

If both remain near 80–88 MiB instead, the fixed-raw explanation regains support.

## Primary outcomes

- MemoryHigh event delta during scan
- maximum scan memory.current
- post-scan memory.current
- post-scan file residency
- onset bracket by hot-anon setting

## Derived coordinates

For each cell derive:

- `peak_fraction_of_high`
- `headroom_over_hot_mib = MemoryHigh - hot_anon`
- `post_scan_live_floor_mib`
- `knee_plus_hot_mib` at the interval level
- `effective_floor_interval = MemoryHigh - knee_interval`
- `non_hot_floor_interval = effective_floor_interval - hot_anon`

The direct mechanism test is whether transformed onset intervals overlap more consistently after accounting for hot/live-set size.

## Secondary outcomes

Retain:

- advice-call count
- pgscan / pgsteal
- hot retouch cost
- scan elapsed / throughput

Hosted timing remains descriptive and must not select a default.

## Pseudo-Council

- **Systems:** vary the live-set axis now because STRATA-005 already varied pressure.
- **Causal inference:** changing MemoryHigh and hot anon simultaneously would destroy the mechanism test.
- **Statistics:** four blocks per cell remain a directional screen; do not fit a precise controller coefficient.
- **Economics:** omit low-information 48 MiB and avoid repeating the 64 MiB-hot anchor.
- **OSS portability:** this remains one hosted substrate; no system-wide default follows.
- **Authority:** design freeze grants no implementation, launch, local execution, retry, or deployment authority.

Consensus:

**freeze STRATA-006 as a fixed-pressure, variable-live-set test.**

## Naming note

The earlier Naive-N0.5-Flash intake proposed a possible future STRATA-006 semantic-reuse study. That was explicitly a proposal, not a decision or reserved execution slot.

The direct mainline mechanism test receives STRATA-006. Semantic reuse remains queued as a later study candidate.

## Monte Carlo

Deferred.

STRATA-006 directly measures the missing axis. A Monte Carlo model before those observations would still require an invented live-set/threshold-jitter distribution.

## Launch boundary

This document freezes design only.

Implementation is a separate bounce.
Hosted launch is a later separate explicit action.
No local-PC execution is authorized.
