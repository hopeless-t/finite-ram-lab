# Research Charter

> **Status:** FROZEN

## Research subject

Finite RAM Lab studies how finite physical RAM is allocated to actual application demand, beginning with Linux systems under memory pressure.

The first concrete observation unit is the Linux memory page.

Page-level control is **not** assumed to be the optimal abstraction.

## Core research question

> Can application-agnostic observation of application demand and operating-system memory state explain where finite RAM becomes a performance bottleneck, and can that evidence later justify a smaller or better coordination mechanism?

## Initial hypotheses

### H1 — Capacity versus management

Some performance degradation under memory pressure may be caused by residency or reclaim decisions rather than fundamental physical-capacity shortage.

### H2 — Dual-sided observability

Application-side state and OS-side memory state contain complementary information. A synchronized timeline may distinguish bottleneck classes that either side alone cannot explain.

### H3 — Coordination gap

If a reproducible information gap exists between application demand and OS residency decisions, selectively closing that gap may reduce the physical-memory requirement for a target performance level.

These are hypotheses to test, not assumed truths.

## Primary performance concept

For workload `W`, define `M_epsilon(W)` as the minimum physical-memory budget that keeps user-visible performance degradation within `epsilon` of a high-memory baseline.

The long-term objective is to determine whether `M_epsilon(W)` can be reduced without unacceptable increases in:

- CPU overhead;
- I/O overhead;
- tail latency;
- memory-management stalls.

The project does not collapse these dimensions into one arbitrary weighted score.

## Research order

```text
Observe
  ↓
Characterize
  ↓
Explain
  ↓
Reproduce
  ↓
Modify
  ↓
Compare
```

Characterization precedes optimization.

## Initial scope

Primary subjects:

- finite physical memory;
- reclaimable application memory;
- anonymous and file-backed memory;
- working-set behavior;
- memory pressure;
- residency and reclaim behavior;
- faults and refaults;
- swap interactions;
- application phase/demand telemetry;
- OS pressure/reclaim telemetry.

Observed when relevant, but not initially optimized:

- compression;
- THP / huge pages;
- kernel-memory consumption;
- compaction;
- I/O scheduling;
- filesystem behavior.

Initially out of scope:

- GPU / VRAM;
- LLM-specific memory management;
- application-specific hard-coded policy;
- custom allocators;
- memory-leak detection;
- NUMA optimization;
- CXL / heterogeneous-memory hardware;
- new compression algorithms;
- a complete custom kernel.

## Integrity rules

A negative result is valid.

Existing Linux behavior being sufficient is a valid result.

The repository exists to discover where finite RAM fails and why, not to prove that a new memory manager is necessary.
