# STRATA-003 Council — Release Cadence Sweep

> **Status:** COUNCIL CONVERGED / PILOT AUTHORIZED FOR FREEZE
> **Parent evidence:** STRATA-002-PILOT-v1
> **Product relevance:** finite-ram-helper API cadence

## Motivation

STRATA-002 showed that per-4 MiB sliding POSIX_FADV_DONTNEED can reduce retained COLD file-cache pressure to approximately the O_DIRECT reference level in the tested workload.

The next OSS-critical question is not whether DONTNEED can work.

It is:

> How frequently must an application release already-consumed COLD ranges to avoid transient pressure, and where is the practical cadence knee?

A helper that advises too frequently may add syscall overhead.

A helper that advises only at end-of-stream may leave final memory clean but still permit large transient page-cache growth and MemoryHigh throttling during the scan.

## Linux behavior relevant to design

Linux `POSIX_FADV_DONTNEED` attempts to free cached pages associated with the specified range and is explicitly useful for periodically freeing already-used data while streaming large files.

Partial-page discard requests are ignored, so release ranges must be page aligned.

Source:

https://man7.org/linux/man-pages/man2/posix_fadvise.2.html

## Frozen read path

Keep ordinary buffered `preadv` and the same reusable 4 MiB scratch buffer in every non-direct arm.

Read chunk size stays constant at 4 MiB.

Only the **release cadence** changes.

## Candidate arms

1. `buffered`
   - no DONTNEED after consumption.

2. `dontneed_4m`
   - release every completed 4 MiB.

3. `dontneed_8m`
   - release every completed 8 MiB.

4. `dontneed_16m`
   - release every completed 16 MiB.

5. `dontneed_32m`
   - release every completed 32 MiB.

6. `dontneed_96m`
   - release only after the full 96 MiB stream has completed.
   - this is the end-of-stream-only arm.

7. `direct`
   - O_DIRECT reference only.

All DONTNEED ranges are page aligned.

## Memory shape

Reuse the strongest STRATA-002 transition condition:

- MemoryHigh: 160 MiB;
- MemoryMax: 320 MiB;
- HOT anonymous guardrail: 64 MiB;
- COLD file: 96 MiB;
- read buffer: 4 MiB.

## Primary outcomes

The key distinction is **transient pressure vs final cleanup**.

Measure:

1. `memory.events:high` delta during scan;
2. maximum observed `memory.current` during scan;
3. post-scan `memory.current`;
4. post-scan file residency.

The current STRATA-002 workload only snapshots before/after scan.

STRATA-003 must therefore add bounded in-process checkpoints after every 4 MiB read to observe scan-time peak memory without external polling.

## Secondary outcomes

- advice call count;
- scan time;
- throughput MiB/s;
- pgscan / pgsteal deltas;
- HOT anonymous residency;
- HOT retouch time;
- swap / OOM;
- final cgroup file bytes.

## Product-facing derived metrics

### Pressure Avoidance Efficiency (PAE)

For each cadence vs buffered:

`1 - high_events(cadence) / high_events(buffered)`

when baseline high events > 0.

### Transient Footprint Reduction (TFR)

Using max scan-time `memory.current`:

`1 - peak_scan_memory(cadence) / peak_scan_memory(buffered)`

### Final Footprint Reduction (FFR)

Using post-scan `memory.current`.

### Advice Density (AD)

`advice_calls / GiB_consumed`

This exposes syscall frequency as an implementation cost proxy.

### Scan-Time Cost Ratio (SCR)

paired scan time ratio vs buffered.

## Pilot design

- 8 independent hosted-runner blocks;
- 7 arms;
- one trial per arm per block;
- 56 total trials;
- deterministic shuffled arm order.

This remains a pilot / response-surface study.

No winner is selected solely from a median.

## Expected decision shape

The useful cadence is the coarsest interval that:

- keeps high-event suppression near the 4 MiB arm;
- keeps transient peak memory materially below buffered;
- ends with low COLD cache retention;
- does not create a clearly worse or unstable scan-time envelope.

The product goal is **not** "smallest interval wins".

It is to find the largest safe release batch.

## Stop conditions

Invalidate a trial if:

- pre-scan file residency > 10%;
- DONTNEED call fails;
- release range is not page aligned;
- full 96 MiB span is not processed;
- content integrity fails;
- OOM occurs;
- direct reference falls back.

## Authority boundary

Hosted pilot only.

No local execution or OSS default cadence is authorized by this Council.
