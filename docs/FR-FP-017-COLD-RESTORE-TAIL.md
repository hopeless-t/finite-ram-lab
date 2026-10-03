# FR-FP-017 — Fixed-size cold restore tail and temporal trace

Status: **HOSTED PHYSICAL TAIL TRACE CANDIDATE**

Parent: **FR-FP-016**

## Why

FR-FP-016 rejected two overly simple models:

- one universal COLD bandwidth;
- one stable state-size knee.

Across three hosted runs, the same 8 MiB COLD restore median moved by almost
30x.

Therefore the next experiment freezes state size and measures the latency
distribution itself.

## Fixture

State size:

    8 MiB

Paired blocks:

    32

Arms:

- WARM_PAGECACHE;
- COLD_DONTNEED.

Order alternates by block.

Physical residency and state-integrity gates remain unchanged.

## Metrics

For WARM and COLD:

- min;
- p50;
- p90;
- p95;
- max;
- mean;
- standard deviation;
- coefficient of variation;
- p95 / p50;
- lag-1 correlation of log latency.

For COLD deadline risk:

    5 ms
    10 ms
    25 ms
    50 ms
    100 ms
    200 ms

For every deadline record:

- miss count;
- miss rate;
- longest consecutive miss run.

## Run-level regime context

The trace is compared with prior hosted 8 MiB COLD medians:

- 4.750 ms;
- 140.907 ms;
- 87.643 ms.

The new run is not expected to reproduce any one median.

Instead it becomes another observed regime.

## Why this matters

A Governor with a hard deadline should not use:

    expected restore latency

when the distribution has large tails or latent regimes.

The relevant quantity is closer to:

    P(restore latency > deadline | current tier / regime)

A later model may condition that probability on observed recent restore
latencies if temporal state is detectable.

## Claim ceiling

**HOSTED_LINUX_FIXED_8MIB_RESTORE_TAIL_TRACE_ONLY**
