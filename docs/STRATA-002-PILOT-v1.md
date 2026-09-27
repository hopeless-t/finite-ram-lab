# STRATA-002-PILOT-v1

> **Status:** FROZEN PILOT CONTRACT
> **Purpose:** characterize practical Linux COLD-stream advice
> **Parent:** STRATA-001-PILOT-v1

## Question

Can ordinary buffered file reading reduce page-cache pressure by explicitly declaring one-shot/COLD semantics, while avoiding O_DIRECT's alignment constraints?

## Frozen environment

- GitHub-hosted Ubuntu 24.04
- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- HOT anonymous guardrail: 64 MiB
- COLD file: 96 MiB
- reusable read buffer: 4 MiB

## Arms

### buffered

Ordinary sequential `preadv`.

No cache advice.

### buffered_noreuse

Ordinary sequential `preadv`.

Before the scan, apply:

`POSIX_FADV_NOREUSE`

to the full file.

Linux 6.3+ is required for the page-replacement semantics being studied.

If the kernel is older, classify the arm/environment as capability hold rather than pretending the advice was meaningful.

### buffered_dontneed

Ordinary sequential `preadv`.

After each completed 4 MiB page-aligned chunk, apply:

`POSIX_FADV_DONTNEED`

to that consumed range.

The return code must be captured.

### direct

O_DIRECT + preadv.

This is the reference for page-cache bypass, not a presumed preferred production mechanism.

## Schedule

Eight independent runner blocks.

Each block executes each arm exactly once in deterministic shuffled order.

Total:

`8 blocks × 4 arms = 32 trials`

## Pre-scan coldness

Before each trial scan:

- POSIX_FADV_DONTNEED on the full file;
- wait briefly for state observation;
- file residency <= 0.10.

Otherwise the trial is invalid.

## HOT guardrail

The 64 MiB anonymous region is faulted and warmed before the file scan.

It is not touched during the scan.

Immediately after scan:

- observe HOT residency;
- observe file residency and cgroup state;
- retouch HOT region.

HOT residency is not the primary endpoint in STRATA-002.

## Primary outcomes

During/after the file scan:

1. `memory.events:high` delta;
2. `memory.current`;
3. `memory.peak`;
4. post-scan file residency.

## Secondary outcomes

- scan time;
- total work time;
- pgscan / pgsteal deltas during scan;
- cgroup file bytes;
- HOT residency;
- HOT retouch latency;
- swap / OOM.

## Pilot interpretation

This is not a throughput benchmark winner-selection exercise.

An advisory arm is promising only if it reduces pressure relative to ordinary buffered I/O **without** a large or unstable latency penalty.

The direct arm establishes a practical lower bound on cache participation, not an authority to recommend O_DIRECT globally.

## Monte Carlo boundary

Only an advisory arm that materially changes the pressure outcome earns a later confirmatory sizing study.

If neither advisory arm moves pressure, record the negative result and move to the cross-process foreground/background study.

## Individual-PC relevance

A positive result could support opt-in application helpers for:

- local-model or dataset streaming;
- large one-shot build artifact reads;
- backup/index passes;
- other semantically COLD sequential reads.

Reused data should remain eligible for normal page caching.

## Attribution

The research direction traces back to Strata's explicit SSD/RAM tiering, while this experiment uses standard Linux APIs and an independent implementation.

## Authority boundary

Research only.
