# REC-004 Pre/Post Observer Hygiene Design v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Motivation

REC-003 showed that the current residency observer can add a target-size-dependent cgroup footprint.

Current STRATA ordering is:

`scan -> _file_residency() -> hot residency -> post_scan cgroup snapshot`

Therefore the historical `post_scan memory.current` is a post-observer quantity.

The robust pressure-event knee remains valid because it is captured during scan, before the residency observer.

## Question

If workload floor is sampled immediately after the scan and before `_file_residency()`, does the apparent capacity-dependent sub-MiB floor growth disappear?

## Paired within-trial design

Each trial captures both:

1. **pre-observer floor**
   - immediately after scan returns;
   - before any post-scan mincore/residency observation;

2. **post-observer floor**
   - after the same existing `_file_residency()` call;
   - same cgroup, same process, same trial.

This creates a paired observer delta without relying on separate-run subtraction.

## Frozen workload

Hosted runner:

`ubuntu-26.04`

Constants:

- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- read chunk 4 MiB
- release cadence: DONTNEED 64 MiB
- cold file prepared cold before each trial

Vary only cold-file capacity:

- 96 MiB
- 192 MiB
- 384 MiB

## Why DONTNEED 64 MiB

The 64 MiB cadence is safely below the observed 80–88 MiB pressure-event knee across the capacity series.

Using a single safe cadence avoids mixing observer hygiene with the separate knee-discovery question.

## Trial budget

- 3 capacities
- 4 independent blocks
- 12 trials

Size order is deterministic-randomized per block.

## Required snapshots

Per trial preserve:

- before_scan
- post_scan_pre_observer
- post_scan_post_observer
- post_retouch

Also preserve:

- MemoryHigh event delta during scan
- file post-residency result
- max scan memory.current
- hot integrity checks
- no-OOM checks

## Derived metrics

For each trial:

`observer_current_delta = post_scan_post_observer - post_scan_pre_observer`

and:

`pre_observer_non_hot_floor = post_scan_pre_observer.memory_current - hot_anon_bytes`

`post_observer_non_hot_floor = post_scan_post_observer.memory_current - hot_anon_bytes`

Primary questions:

- Does pre-observer non-hot floor remain bounded across 96/192/384 MiB?
- Does paired observer_current_delta increase at 384 MiB in the same direction as REC-003?
- Does file residency remain zero?

## Historical migration rule

Do not rewrite historical raw evidence.

Historical STRATA summaries keep their original fields and are annotated as:

`post_observer_floor_legacy`

where relevant.

New studies must name the clean quantity explicitly:

`post_scan_pre_observer`

and may retain a separate diagnostic:

`post_scan_post_observer`.

## Acceptance

Measurement hygiene is validated if:

- all 12 trials PASS;
- pre-observer floor is capacity-bounded at sub-MiB scale;
- paired post-minus-pre observer delta reproduces size-dependent contamination directionally;
- scan MemoryHigh behavior remains zero at 64 MiB cadence.

No requirement is imposed that the observer delta be numerically identical to REC-003, because allocator/cgroup charging is quantized.

## Pseudo-Council

- **Measurement:** paired within-trial subtraction is stronger than comparing separate runs.
- **Systems:** preserve the existing observer implementation to measure the actual contamination path.
- **Statistics:** four paired observations per capacity are directional validation, not a smooth scaling fit.
- **Evidence:** raw historical measurements remain immutable; semantic labels change prospectively.
- **Authority:** design freeze grants no launch or deployment authority.

Consensus:

**freeze REC-004 as a paired pre/post-observer hygiene validation across the 96/192/384 MiB capacity series.**

## Launch boundary

Design only.
Implementation and launch are separate bounces.
No local-PC execution.
