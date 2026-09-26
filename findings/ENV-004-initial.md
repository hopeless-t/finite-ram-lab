# ENV-004 Initial Finding

> **Status:** SELECTIVE CAPABILITY CONFIRMED  
> **Run:** 36227867747

## Question

Can a swap-backed anonymous target range be proactively reclaimed out of RAM while an equal matched control range remains resident?

## Frozen probe

- 4 independent GitHub-hosted runner blocks;
- 2 balanced target identities per block;
- 8 total trials;
- target mapping: 16 MiB;
- matched control mapping: 16 MiB;
- target only receives `MADV_PAGEOUT`;
- proactive reclaim request: `16M swappiness=max`;
- low-pressure cgroup: MemoryHigh 256 MiB, MemoryMax 320 MiB.

## Result

All eight trials completed successfully.

Aggregate:

    classification = SELECTIVE
    pageout success = 8 / 8
    proactive reclaim success = 8 / 8
    content integrity = 8 / 8
    OOM events = 0

Residency after proactive reclaim:

    target median resident fraction = 0.0000
    target maximum resident fraction = 0.00488
    control median resident fraction = 1.0000
    control minimum resident fraction = 1.0000
    median selectivity gap = 1.0000

Timing:

    target median retouch = 103.53 ms
    control median retouch = 0.354 ms

Swap:

    median swap growth after target pageout = 16.0 MiB
    median swap growth after reclaim = 16.88 MiB

## Interpretation

The prepared target range became almost completely nonresident while the matched control mapping remained fully resident.

This closes the research-instrument gap left by ENV-003 v2.

The two-stage operation:

    target MADV_PAGEOUT
          ↓
    target gains anonymous swap backing
          ↓
    cgroup memory.reclaim with swappiness=max
          ↓
    target becomes nonresident
    matched control remains resident

is sufficiently selective on the tested hosted environment to support a matched causal intervention experiment.

## What this does not establish

ENV-004 does not show:

- that the kernel made a bad natural eviction decision;
- that semantic application information improves memory management;
- that explicit pageout/reclaim is a desirable production mechanism;
- that a userspace coordination layer is justified.

It validates an experimental instrument only.

## Next research question

> Holding live memory, semantic regions, reclaim amount, and later workload constant, does selectively making the soon-reused region nonresident cause materially larger next-use latency than selectively making a matched not-next-used region nonresident?

This should be a paired randomized experiment across independent hosted-runner blocks.
