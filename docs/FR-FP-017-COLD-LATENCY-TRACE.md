# FR-FP-017 — Long 8 MiB COLD restore temporal trace

Status: **HOSTED PHYSICAL TEMPORAL-TRACE CANDIDATE**

Parent: **FR-FP-016**

## Why

FR-FP-016 rejected a stationary state-size-only COLD restore model.

Across three independent hosted runs, the 8 MiB COLD median moved by almost
30x.

The next experiment removes state-size variation and spends the sample budget on
time.

## Frozen trace

State size:

    8 MiB

Paired blocks:

    48

Each block contains:

- WARM_PAGECACHE restore;
- COLD_DONTNEED restore.

Arm order alternates by block.

The WARM arm remains an environmental control.

## Measurements

For each arm:

- min;
- p50;
- p90;
- p95;
- p99;
- max;
- mean;
- standard deviation;
- coefficient of variation;
- lag-1 / lag-2 / lag-4 autocorrelation;
- deadline miss rates at 5/10/25/50/100/200 ms.

For COLD, also compute burst structure above:

- 25 ms;
- 50 ms;
- 100 ms.

The 48 samples are divided into four contiguous 12-block epochs and each epoch
gets p50 and p95.

## No directional burst gate

This lane is exploratory.

It does not require:

- positive autocorrelation;
- a specific number of bursts;
- a specific p99;
- a particular deadline-miss rate.

Those are observations, not desired outcomes.

Qualification only requires:

- all 48 paired blocks;
- exact restore integrity;
- WARM physically resident before restore;
- COLD physically nonresident before restore;
- COLD median slower than WARM;
- ordered tail quantiles.

## Next analysis

The resulting trace will be compared against shuffled / iid controls.

Questions:

- are slow restores clustered beyond an iid Bernoulli baseline?
- is lag structure stronger than shuffled traces?
- do contiguous epoch medians drift?
- does WARM show the same temporal state, or is it COLD-specific?

Only after that analysis should the Governor gain a latent I/O-state model.

## Claim ceiling

**HOSTED_8MIB_COLD_RESTORE_TEMPORAL_TRACE_PILOT_ONLY**
