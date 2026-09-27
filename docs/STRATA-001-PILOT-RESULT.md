# STRATA-001-PILOT-v1 Recovered Result

> **Status:** PASS / PILOT ONLY
> **Source run:** `36336994450`
> **Physical trials:** 36 / 36 valid
> **Runner blocks:** 6 / 6
> **Attribution:** inspired by https://github.com/Niko1221/Strata

## Recovery provenance

All six physical block jobs in run `36336994450` completed successfully.

The original aggregate job failed only because the collector did not recognize the artifact download directory name `strata001-pilot-block-<N>`.

Collector fix:

- commit: `71612c6b37dcfe5a9d332f5c8d0f9d1ed444d280`
- CI run: `36337262716`
- CI conclusion: `success`

The exact six block artifacts were recovered and aggregated without repeating the physical trials.

## Validity

All frozen execution checks passed:

- 6 runner blocks present;
- 36 trials present;
- all trials PASS;
- all cells present exactly once per block;
- no OOM;
- direct I/O never fell back;
- every file was cold before scan;
- HOT content integrity preserved.

## Primary pilot result

The frozen primary pilot estimand was:

`HOT residency(DIRECT_PREAD) - HOT residency(BUFFERED_PREAD)`

At both MemoryHigh levels, the paired block difference was exactly zero in every block.

| MemoryHigh | DIRECT median HOT residency | BUFFERED median HOT residency | Paired diff |
| ---: | ---: | ---: | ---: |
| 160 MiB | 1.0000 | 1.0000 | 0.0000 |
| 168 MiB | 1.0000 | 1.0000 | 0.0000 |

MMAP also retained HOT residency at 1.0000 in every trial.

Therefore this pilot exposed **no HOT-anonymous preservation opportunity** for direct I/O in the tested same-cgroup file-pressure regime.

This is a pilot finding, not a generalized claim about Linux or arbitrary PCs.

## File-cache separation

The mechanism itself remained strong.

Median post-scan file residency:

| MemoryHigh | MMAP | BUFFERED_PREAD | DIRECT_PREAD |
| ---: | ---: | ---: | ---: |
| 160 MiB | 0.8659 | 0.8737 | 0.0000 |
| 168 MiB | 0.9531 | 0.9349 | 0.0000 |

Median cgroup file bytes before HOT retouch:

| MemoryHigh | MMAP | BUFFERED_PREAD | DIRECT_PREAD |
| ---: | ---: | ---: | ---: |
| 160 MiB | 83.13 MiB | 83.88 MiB | 0.00 MiB |
| 168 MiB | 91.50 MiB | 89.77 MiB | 0.00 MiB |

## Pressure behavior

Median cgroup memory.current before HOT retouch:

| MemoryHigh | MMAP | BUFFERED_PREAD | DIRECT_PREAD |
| ---: | ---: | ---: | ---: |
| 160 MiB | 159.86 MiB | 159.79 MiB | 75.86 MiB |
| 168 MiB | 167.86 MiB | 165.90 MiB | 75.86 MiB |

Median `memory.events:high` increments during the file scan:

| MemoryHigh | MMAP | BUFFERED_PREAD | DIRECT_PREAD |
| ---: | ---: | ---: | ---: |
| 160 MiB | 50.5 | 6.0 | 0.0 |
| 168 MiB | 17.0 | 2.0 | 0.0 |

No trial used swap before HOT retouch.

Interpretation:

- buffered and mmap scans materially populated file cache and drove the cgroup toward MemoryHigh;
- direct I/O avoided that memory footprint and avoided MemoryHigh events;
- nevertheless Linux preserved the HOT anonymous region completely in this regime.

## Latency observations

Median HOT-retouch latency was approximately 1.85–1.91 ms in all arms.

The direct/buffered total-work ratios were highly variable across the six blocks.

Median ratio:

- 160 MiB: `0.9291`
- 168 MiB: `0.8793`

Individual block ratios ranged widely, so this pilot does **not** support a throughput claim.

## Scientific consequence

Do not spend confirmatory sample size on the current primary endpoint.

The current tested environment already protected HOT anonymous memory while reclaiming/throttling file-backed pressure.

The next useful question is more practical:

> Can a normal buffered streaming path shed semantically COLD file cache explicitly, avoiding most of the pressure footprint of buffered I/O without taking on the alignment and portability constraints of O_DIRECT?

That motivates a `BUFFERED + POSIX_FADV_DONTNEED` study.

## Individual-PC relevance

This result suggests a personal-PC optimization should be application-specific rather than a global kernel policy.

Candidate use cases are one-shot or low-reuse large reads such as:

- model shards / lookup tables;
- large build or analysis artifacts;
- indexing / backup scans;
- media or dataset passes.

For reused data, page cache is useful and should not be disabled blindly.

## Authority boundary

Pilot only.

No generalized recommendation to use O_DIRECT is authorized.
