# STRATA-002 Council — Advisory Cold-Stream Cache Control

> **Status:** COUNCIL CONVERGED / DESIGN AUTHORIZED
> **Parent evidence:** STRATA-001-PILOT-v1
> **Original inspiration:** https://github.com/Niko1221/Strata

## Why the question changes

STRATA-001-PILOT-v1 found:

- O_DIRECT strongly separated COLD file traffic from page cache;
- BUFFERED/MMAP accumulated roughly 84–92 MiB of file-cache memory;
- BUFFERED/MMAP produced MemoryHigh events;
- O_DIRECT produced none in the tested cells;
- HOT anonymous residency remained 1.0000 in every trial and arm.

Therefore the tested kernel already protected HOT anonymous memory against this file-backed pressure.

The useful next question is no longer:

> can O_DIRECT save HOT anonymous pages here?

Instead:

> can an ordinary buffered streaming application tell Linux that data are one-shot/COLD, reducing avoidable page-cache pressure without the alignment and portability constraints of O_DIRECT?

## Linux mechanisms

Linux `posix_fadvise(2)` exposes two relevant advisory controls.

### POSIX_FADV_NOREUSE

The file data are expected to be accessed once.

On Linux 6.3 and newer, the page replacement algorithm may ignore access to page-cache pages marked by this advice.

Reference:

https://man7.org/linux/man-pages/man2/posix_fadvise.2.html

### POSIX_FADV_DONTNEED

The specified file range is not expected to be accessed in the near future and Linux attempts to free cached pages for that range.

For a streaming application, applying this to already-consumed aligned chunks may reduce transient COLD cache retention while preserving ordinary buffered-read semantics.

## Candidate directions considered

### A — force lower MemoryHigh until HOT anon finally falls

Rejected as the next step.

This would intentionally search for an extreme failure boundary after the kernel already showed correct file-vs-anon discrimination in the tested regime.

It has lower near-term relevance to normal personal-PC optimization.

### B — jump directly to cross-process foreground/background interference

Deferred.

This is externally realistic, but it adds process orchestration and attribution complexity before the advisory mechanisms themselves are characterized.

### C — compare buffered advice against O_DIRECT

**Adopted.**

This is the smallest bridge from the Strata-inspired result to a practical application optimization.

## Study name

**STRATA-002 — Advisory Cold-Stream Cache Control**

## Arms

1. `buffered`
   - ordinary buffered `preadv`;
   - no cache advice.

2. `buffered_noreuse`
   - ordinary buffered `preadv`;
   - apply `POSIX_FADV_NOREUSE` to the full file before the scan.

3. `buffered_dontneed`
   - ordinary buffered `preadv`;
   - after each completed 4 MiB aligned chunk, apply `POSIX_FADV_DONTNEED` to the consumed range.

4. `direct`
   - O_DIRECT + preadv;
   - reference arm, not presumed winner.

## Pilot pressure

Use only `MemoryHigh=160 MiB` initially.

Reason:

STRATA-001 saw the stronger buffered pressure signal there:

- BUFFERED median MemoryHigh events during scan: 6;
- MMAP median: 50.5;
- DIRECT median: 0.

Using one pressure level keeps the next experiment atomic.

MemoryMax remains 320 MiB.

## Memory shape

Reuse:

- HOT anonymous guardrail: 64 MiB;
- COLD file: 96 MiB;
- reusable read buffer: 4 MiB.

HOT anonymous residency remains a **guardrail**, not the primary endpoint.

## Primary outcomes

Per trial:

- delta in `memory.events:high` during the file scan;
- cgroup `memory.current` immediately after scan;
- cgroup `memory.peak`;
- post-scan file residency.

## Secondary outcomes

- scan elapsed time;
- total work time;
- pgscan / pgsteal scan deltas;
- cgroup file bytes;
- HOT anonymous residency;
- HOT retouch latency;
- swap / OOM.

## Practical success shape

An advisory arm is interesting for personal-PC software if it:

- materially reduces file-cache footprint and MemoryHigh pressure relative to normal buffered reads;
- keeps ordinary buffered I/O semantics;
- does not impose a large or unstable scan-time cost;
- preserves HOT-content correctness;
- remains fail-open only in the sense of performance advice: unsupported advice must be explicitly reported, never silently interpreted as a successful mechanism.

## Pilot design

- 8 independent runner blocks;
- 4 arms;
- one trial per arm per block;
- 32 total trials;
- deterministic shuffled order within block.

This is an effect/variance pilot.

No p-value gate.

## Why 8 blocks

STRATA-001 showed large block-to-block timing variation.

Two extra blocks over the previous pilot give a slightly better first estimate of latency variability without turning this into a confirmatory campaign.

## Monte Carlo boundary

Do not perform confirmatory sizing until this pilot identifies which advisory arm, if any, actually changes the pressure outcome.

If both advisory arms are ineffective, record that negative result and move to the cross-process study rather than inflating sample size.

## Personal-PC path if successful

A successful advisory mechanism could become:

- a small library/helper for large one-shot file readers;
- an opt-in wrapper around dataset/model/build-artifact scanning;
- a future finite-ram planner action chosen only when data are declared COLD/one-shot.

It must not become a global "drop caches" policy.

## Attribution

STRATA-002 grows from the Strata-inspired finding but uses Linux standard advisory interfaces and independent finite-ram-lab implementation.

No Strata source code is copied.

## Authority boundary

Bounded research only.
No global kernel tuning or deployment is authorized.
