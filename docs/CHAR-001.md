# CHAR-001 — Memory-Pressure Dose–Response Characterization

> **Status:** IMPLEMENTED / INITIAL CONTRACT

## Question

Does the latency increase observed in OBS-001 form a reproducible dose–response relationship as the cgroup memory-pressure threshold is varied?

## Why this experiment

OBS-001 established synchronized application/OS observability and showed a large latency increase during `HOTSET_RETOUCH` while reclaim, swap, and `memory.high` activity increased.

That was a single observation.

CHAR-001 asks whether the phenomenon is a repeatable pressure-dependent regime rather than a coincident one-off event.

## Controlled workload

The application state machine remains the OBS-001 workload:

```text
BASELINE
  ↓
HOTSET_ALLOC
  ↓
HOTSET_TOUCH
  ↓
BURST_ALLOC
  ↓
HOTSET_RETOUCH
  ↓
BURST_RELEASE
  ↓
COMPLETE
```

The live semantic workload is held constant:

- hot set: 64 MiB;
- burst: 96 MiB;
- `MemoryMax`: 320 MiB.

Only `MemoryHigh` is swept.

## Pressure levels

```text
96, 112, 128, 144, 160, 192, 224, 256 MiB
```

Each level is repeated 12 times.

Execution order is deterministically shuffled from the declared seed so monotonic drift is not confounded with pressure level.

All trials execute sequentially on one hosted runner for the initial characterization run.

## Primary outcome

```text
HOTSET_RETOUCH phase latency
```

Secondary observations include:

- `memory.events:high`;
- `pgscan`;
- `pgsteal`;
- page faults and major faults;
- swap usage;
- cgroup memory PSI;
- memory.current.

All secondary counters are evaluated as within-trial deltas from BASELINE to HOTSET_RETOUCH where appropriate.

## Statistical treatment

For each `MemoryHigh` level the analysis records:

- median latency;
- p90 latency;
- bootstrap 95% interval for the median;
- median swap growth;
- median scan/steal growth;
- median `memory.high` event count;
- median PSI stall growth.

The existing `frl changepoint` calculator is then applied to the level-wise median latency curve.

The breakpoint is a characterization aid, not automatically a physical critical point.

## Acceptance

Scientific execution PASS requires:

1. every scheduled trial produced valid structured evidence;
2. every workload trial passed its OBS checks;
3. no OOM event occurred;
4. every declared pressure level has the declared number of repeats.

CHAR-001 does **not** require latency to increase.

A flat or contradictory curve is a valid finding.

## Threats to validity

The initial run deliberately keeps trials on one GitHub-hosted runner to reduce between-runner variation.

That introduces within-run temporal dependence and does not establish cross-runner reproducibility.

If a pressure-dependent regime is observed, the next validation step should reproduce selected levels across independent hosted runners.

## Decision boundary

CHAR-001 may identify a reproducible bottleneck regime.

It does not yet decide whether that regime is caused by:

- fundamental capacity shortage;
- reclaim timing;
- residency mismatch;
- swap cost;
- missing application information;
- another mechanism.

Mechanism attribution comes later.
