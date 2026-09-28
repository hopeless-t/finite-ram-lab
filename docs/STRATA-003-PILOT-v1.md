# STRATA-003-PILOT-v1

> **Status:** FROZEN PILOT CONTRACT
> **Purpose:** DONTNEED release-cadence response surface

## Frozen workload

- runner: GitHub-hosted Ubuntu 24.04
- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- HOT anonymous guardrail: 64 MiB
- COLD file: 96 MiB
- buffered read chunk: 4 MiB
- scan-time checkpoint cadence: 4 MiB

## Arms

| Arm | DONTNEED cadence |
| --- | ---: |
| buffered | none |
| dontneed_4m | 4 MiB |
| dontneed_8m | 8 MiB |
| dontneed_16m | 16 MiB |
| dontneed_32m | 32 MiB |
| dontneed_96m | 96 MiB / end of stream |
| direct | O_DIRECT reference |

All non-direct arms perform the same ordinary buffered `preadv` reads with the same 4 MiB reusable scratch buffer.

Only cache-release cadence differs.

## Why scan-time checkpoints matter

A final post-scan DONTNEED can make the final footprint look excellent while allowing the process to hit MemoryHigh repeatedly during the scan.

Therefore, after each completed 4 MiB read, record bounded in-process:

- `memory.current`;
- `memory.events:high`;
- cgroup file bytes;
- swap.current.

No external polling is used.

The primary transient-footprint value is the maximum observed `memory.current` across these scan checkpoints.

## Release algorithm

For a DONTNEED arm:

1. accumulate completed read bytes;
2. whenever the completed-but-not-released range reaches the arm's cadence, advise exactly that aligned range as DONTNEED;
3. after the final read, release any remaining completed aligned bytes;
4. record every advice call and range.

For `dontneed_96m`, the only advice call occurs after the full file has been read.

## Primary outcomes

- MemoryHigh event delta during scan;
- maximum scan-time memory.current;
- post-scan memory.current;
- post-scan file residency.

## Secondary outcomes

- advice call count;
- scan elapsed;
- throughput MiB/s;
- pgscan / pgsteal;
- HOT residency / retouch;
- swap / OOM;
- post-scan cgroup file bytes.

## Derived metrics

### Pressure Avoidance Efficiency

Relative reduction in MemoryHigh events versus paired buffered baseline.

### Transient Footprint Reduction

`1 - max_scan_memory(cadence) / max_scan_memory(buffered)`

### Final Footprint Reduction

`1 - post_scan_memory(cadence) / post_scan_memory(buffered)`

### Advice Density

`advice_calls / GiB consumed`

### Scan-Time Cost Ratio

paired scan time ratio versus buffered.

## Design

- 8 independent blocks;
- 7 arms;
- 56 trials;
- deterministic shuffled arm order.

Pilot only.

Do not select an OSS default solely from this study.

## Expected product interpretation

A useful cadence is the coarsest release interval that preserves most of the pressure reduction while avoiding unnecessary advice-call density.

The important failure mode to detect is:

> final footprint looks clean, but transient pressure already happened.

## Authority boundary

Hosted research only.
