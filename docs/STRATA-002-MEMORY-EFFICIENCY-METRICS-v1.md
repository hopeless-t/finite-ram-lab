# STRATA-002 Memory-Efficiency Metrics v1

> **Status:** FROZEN DESCRIPTIVE METRICS
> **Source:** STRATA-002-PILOT-v1
> **Run:** `36338522437`
> **Scope:** tested 160 MiB MemoryHigh cgroup workload only

## Why metrics are needed

A raw statement such as "memory.current fell by ~83 MiB" is useful but difficult to compare across:

- different RAM sizes;
- different cgroup limits;
- different COLD-file sizes;
- future local-PC dogfood.

This document freezes a small metric vocabulary for application-level finite-RAM work.

No single synthetic score is used.

## M1 — Resident Footprint Reduction (RFR)

Measures the fraction of observed post-scan resident cgroup footprint removed by an optimization relative to ordinary buffered I/O.

[
RFR = 1 - \frac{M_{optimized}}{M_{buffered}}
]

where `M` is post-scan `memory.current`.

Higher is better.

### STRATA-002 pilot

Paired block values for `buffered_dontneed`:

- minimum: **51.71%**
- median: **52.13%**
- maximum: **52.55%**

Median cgroup footprint:

- ordinary buffered: **159.32 MiB**
- buffered + sliding DONTNEED: **75.86 MiB**

Interpretation:

> in this workload, sliding DONTNEED removed about half of the resident cgroup memory footprint observed after an ordinary one-shot buffered scan.

## M2 — Cold-Stream Amplification Factor (CSAF)

Measures how much resident memory a file-streaming policy consumes relative to the direct-I/O reference under the same HOT/scratch workload.

[
CSAF = \frac{M_{arm}}{M_{direct-reference}}
]

Lower is better.

A value near 1 means the arm approaches the low-cache reference footprint.

### STRATA-002 pilot medians

- ordinary buffered: **2.097×**
- buffered + sliding DONTNEED: **1.000×**
- direct reference: **1.000×**

Interpretation:

> ordinary buffered reading approximately doubled the observed resident cgroup footprint relative to the page-cache-bypass reference; DONTNEED removed almost all of that amplification.

This is a contextual reference metric, not a universal lower bound for arbitrary applications.

## M3 — Recovered Memory Headroom (RMH)

Measures how much distance from a finite memory pressure boundary is recovered.

[
RMH = (H - M_{optimized}) - (H - M_{buffered})
]

which simplifies to:

[
RMH = M_{buffered} - M_{optimized}
]

where `H` is the tested `memory.high`.

Also report normalized recovered headroom:

[
NRH = RMH/H
]

### STRATA-002 pilot median

For `H = 160 MiB`:

- buffered headroom: **0.68 MiB**
- DONTNEED headroom: **84.14 MiB**
- recovered headroom: **83.46 MiB**
- normalized recovered headroom: **52.16% of MemoryHigh**

Interpretation:

> the optimized stream moved the cgroup from essentially sitting on the pressure boundary to retaining roughly half the configured MemoryHigh as unused headroom.

## M4 — Cold Cache Retention Fraction (CCRF)

Measures how much of the one-shot file remains resident after the scan.

Primary observation:

[
CCRF = file\_resident\_fraction_{post-scan}
]

Lower is better only when the application contract declares the data semantically COLD / one-shot.

### STRATA-002 pilot medians

- ordinary buffered: **0.8646**
- buffered + NOREUSE: **0.8542**
- buffered + DONTNEED: **0.0000**
- direct: **0.0000**

The cgroup file-byte view was consistent:

- ordinary buffered: ~**83.0 MiB**
- DONTNEED: ~**0 MiB**

Relative to the 96 MiB COLD file, ordinary buffered retained about **86.5%** worth of file-cache memory in the cgroup at observation time.

## M5 — Pressure Event Suppression (PES)

For blocks where the buffered baseline generates at least one `memory.events:high` increment:

[
PES = 1 - \frac{E_{optimized}}{E_{buffered}}
]

Higher is better.

### STRATA-002 pilot

Every buffered baseline block had 5 or 6 high events.

Every DONTNEED block had 0.

Therefore:

- block-level PES: **100% in 8 / 8 blocks**
- median avoided events: **5**

This metric is useful as a pressure/throttling signal, not as a direct latency measure.

## M6 — Scan-Time Cost Ratio (SCR)

Memory savings are not sufficient for a practical optimization.

[
SCR = \frac{T_{optimized}}{T_{buffered}}
]

Lower is better.

### STRATA-002 pilot: DONTNEED vs buffered

- median SCR: **1.027×**
- geometric-mean SCR: **1.005×**
- observed block range: **0.260× to 2.969×**

The large range means hosted-runner timing is noisy.

Therefore do not summarize this pilot as "2.7% slower" or "0.5% slower" without the variance warning.

The confirmatory design explicitly treats latency as a separate risk guardrail.

## Practical reporting bundle

For future finite-ram experiments, report at least:

1. **RFR** — how much resident footprint fell;
2. **RMH/NRH** — how much finite-memory headroom returned;
3. **CCRF** — whether declared COLD file pages actually left memory;
4. **PES** — whether pressure/throttle events disappeared;
5. **SCR** — what time cost accompanied the memory benefit.

Use **CSAF** when a low-cache reference arm such as O_DIRECT exists.

## Current concise result

For this hosted STRATA-002 workload:

> sliding POSIX_FADV_DONTNEED reduced post-scan resident memory by a paired median of **52.13%**, recovered about **83.46 MiB** of headroom under a 160 MiB MemoryHigh boundary, suppressed observed MemoryHigh events by **100% across 8/8 blocks**, and reduced COLD-file residency from about **86.5% to 0%**. Its scan-time effect remained too noisy for a throughput claim.

## Individual-PC interpretation boundary

These metrics make hosted and future local results comparable.

They do **not** imply that a 20 GiB personal PC will literally gain 52% total system RAM.

The percentage applies to the measured cgroup/workload footprint.

Local dogfood must report the same metrics against a bounded real workload before any system-level claim is made.
