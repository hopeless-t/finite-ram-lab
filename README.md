# Finite RAM Lab

A small, reproducible systems research lab for understanding how ordinary computers behave when physical RAM becomes constrained.

> **Core question:**  
> When physical RAM is limited, what should remain in memory, what should be reclaimed, and when?

## Status

**Systems research / experimental software — early development**

Current phase:

**Observation before coordination**

Finite RAM Lab is currently focused on observing application-side memory demand and operating-system-side memory supply, pressure, reclaim, and performance on a shared timeline.

No new memory-management policy or coordination mechanism is treated as justified until a reproducible bottleneck has been identified.

## Why this project exists

Applications and operating systems observe different parts of the memory problem.

Applications understand the meaning, lifecycle, and phase of their own data.

The operating system understands global physical-memory pressure, contention, residency, reclaim activity, faults, refaults, swap behavior, and system-wide competition.

Finite RAM Lab begins by making both sides observable.

The project asks whether performance degradation under finite RAM is primarily caused by:

- fundamental capacity shortage;
- residency mismatch;
- reclaim timing;
- refault or I/O costs;
- another mechanism revealed by measurement.

The project does **not** assume in advance that existing Linux memory management is inefficient.

## Research principle

```text
Observe
  ↓
Characterize
  ↓
Reproduce
  ↓
Form hypothesis
  ↓
Intervene
  ↓
Compare
```

**Observe before optimizing.**

A new memory-management mechanism should be proposed only after a reproducible bottleneck has been identified.

## Initial experimental platform

The initial platform is a commodity Linux PC.

Linux memory pages are the first observation unit, but page-level control is not assumed to be the optimal abstraction.

The research problem is broader:

> How well does finite physical RAM align with actual application memory demand?

## Evidence principle

Observation is not explanation.

Correlation is not causation.

A refault is not automatically a bad eviction.

High memory utilization is not automatically inefficient.

Free memory is not itself an optimization objective.

A benchmark improvement is not sufficient evidence of a general memory-management improvement.

## Repository status

The repository is being bootstrapped one research contract at a time.

Planned first lane:

```text
OBS-001
Application + OS memory observability baseline
```

Later research stages are intentionally not pre-decided. Their contents will be determined by observed evidence.
