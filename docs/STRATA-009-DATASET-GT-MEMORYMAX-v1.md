# STRATA-009 Dataset-Greater-Than-MemoryMax Design v1

> **Status:** FROZEN DESIGN / NOT IMPLEMENTED / NOT LAUNCHED
> **Authority:** HOSTED_RESEARCH_ONLY

## Question

Can a one-shot cold dataset whose total capacity exceeds the cgroup MemoryMax still be scanned under a bounded DONTNEED policy without increasing the instantaneous resident-memory knee?

Parent evidence:

- STRATA-007: cold=96 MiB
- STRATA-008: cold=192 MiB
- both: `80 MiB < K <= 88 MiB`
- MemoryHigh=160 MiB
- MemoryMax=320 MiB
- hot anon=64 MiB

STRATA-009 moves total cold capacity to:

`384 MiB`

which is:

- 4x the original 96 MiB dataset;
- 2x STRATA-008;
- 2.4x MemoryHigh;
- 1.2x MemoryMax.

## Causal axis

Change only total one-shot cold-file capacity:

- 384 MiB

Hold constant:

- runner: Ubuntu 26.04
- Python: 3.12
- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- hot anon: 64 MiB
- read chunk: 4 MiB
- DONTNEED implementation
- cgroup/systemd-run execution
- environment receipt contract

## Arm panel

Use only bounded-policy arms:

- DONTNEED 64 MiB
- DONTNEED 72 MiB
- DONTNEED 80 MiB
- DONTNEED 88 MiB
- DONTNEED 96 MiB

### Why buffered is intentionally omitted

The question is whether the bounded streaming policy can process a dataset larger than MemoryMax.

A fully buffered arm is already known to create pressure and may legitimately be OOM-killed once total capacity exceeds MemoryMax. The current trial contract treats OOM as invalid and a killed unit may fail before producing a complete scientific receipt.

Including that arm would conflate two questions:

1. whether the bounded policy remains stable;
2. whether the existing harness can preserve evidence across an intentionally unbounded/OOM control.

The unbounded-control evidence problem is a separate Recorder/harness study.

Omitting buffered here narrows the study; it does not assert buffered success.

## Trial budget

- 5 DONTNEED arms
- 4 independent runner blocks
- 20 total trials

## Recorder density

384 MiB / 4 MiB = 96 scan checkpoints.

REC-001 expected density:

`98 records/trial`

= start + 96 samples + end.

This is a mechanical consequence of the existing checkpoint-per-chunk semantics.

## Competing outcomes

### H-bounded-streaming

Dataset capacity can exceed MemoryMax while instantaneous demand stays bounded.

Expected at current resolution:

- DONTNEED 64 / 72 / 80: zero median MemoryHigh events;
- DONTNEED 88 / 96: positive median MemoryHigh events;
- onset remains `80 < K <= 88 MiB`;
- transformed interval remains `144 < K+hot <= 152 MiB`;
- DONTNEED non-hot post-scan floor remains within the prior `[8,16) MiB` interval.

### H-capacity-leak

At 384 MiB total capacity, the bounded policy begins retaining or accumulating state across release intervals.

Evidence would include:

- onset shift downward;
- elevated post-scan non-hot floor;
- nonzero file residency;
- OOM / invalid trials even in low-cadence DONTNEED arms.

## Primary outcomes

- trial validity / OOM
- MemoryHigh events
- maximum memory.current
- post-scan memory.current
- post-scan file residency
- onset bracket
- non-hot resident floor

## Work-scaling outcomes

Also record:

- logical bytes scanned
- advice calls
- scan elapsed time as descriptive only

For a 384 MiB stream, expected advice-call counts are mechanically larger than at 192 MiB.

## Pseudo-Council

- **Finite-RAM:** crossing MemoryMax with total dataset size is a direct test of capacity versus working set.
- **Harness:** omit the intentionally unbounded arm until OOM evidence preservation is explicitly designed.
- **Causal inference:** keep all live-set and pressure parameters fixed.
- **Statistics:** four blocks remain a directional screen.
- **Authority:** design freeze does not grant launch or local execution authority.

Consensus:

**freeze STRATA-009 as a bounded-policy-only 384 MiB capacity boundary test.**

## Monte Carlo

No synthetic Monte Carlo is needed before the physical boundary observation.

Empirical bootstrap may be used after valid samples exist.

## Launch boundary

Design only.
Implementation is a separate bounce.
No local-PC execution.
