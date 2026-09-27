# STRATA-001-PILOT-v1

> **Status:** FROZEN PILOT CONTRACT
> **Purpose:** effect-direction / variance estimation only
> **Inspired by:** https://github.com/Niko1221/Strata

## Design

Six independent GitHub-hosted runner blocks.

Every block runs exactly one trial for each cell:

| MemoryHigh | MMAP | BUFFERED_PREAD | DIRECT_PREAD |
| ---: | :---: | :---: | :---: |
| 160 MiB | 1 | 1 | 1 |
| 168 MiB | 1 | 1 | 1 |

Total:

`6 blocks × 2 pressure levels × 3 arms = 36 trials`

Cell order is deterministically shuffled per block.

## Memory contract

- semantically HOT anonymous region: 64 MiB;
- semantically COLD file: 96 MiB;
- reusable pread buffer: 4 MiB;
- MemoryMax: 320 MiB.

The HOT region is fully faulted before the file scan and not touched during the scan.

The file is scanned once and not reused during the measured interval.

Immediately after the scan:

1. observe HOT anonymous residency;
2. observe file residency and cgroup anon/file state;
3. retouch the entire HOT region.

## Arms

### MMAP

Read-only map the file and touch one byte from every page.

This arm is architectural/descriptive.

Its scan-time cost must not be treated as directly comparable to the pread arms because it does not copy the full 96 MiB through a userspace buffer.

### BUFFERED_PREAD

Read the entire 96 MiB sequentially using ordinary buffered `preadv` into one reusable 4 MiB anonymous mmap buffer.

### DIRECT_PREAD

Read the same span in the same order using `O_DIRECT` + `preadv` into the same-sized aligned reusable buffer.

No silent fallback is allowed.

## File-coldness rule

Before each trial scan:

- fsync preparation must already be complete;
- issue `POSIX_FADV_DONTNEED`;
- observe file residency.

Required:

`pre_scan_file_resident_fraction <= 0.10`

Otherwise the trial is INVALID.

## Primary pilot outcome

For each MemoryHigh level, estimate the paired runner-block difference:

`HOT residency(DIRECT_PREAD) - HOT residency(BUFFERED_PREAD)`

No significance gate is applied.

## Secondary pilot outcomes

For DIRECT_PREAD vs BUFFERED_PREAD:

- log HOT-retouch latency ratio;
- total-work ratio;
- post-scan file residency;
- pre-retouch cgroup anon bytes;
- pre-retouch cgroup file bytes;
- pre-retouch swap.

MMAP remains descriptive/architectural.

## Mechanism-fidelity checks

DIRECT_PREAD must:

- report true direct-I/O path;
- read the full 96 MiB;
- not silently fall back;
- leave the file materially less cached than the buffered arm.

BUFFERED_PREAD and MMAP must read/touch the declared span.

## Trial validity

A trial is valid only if:

- MemoryHigh/MemoryMax match the frozen values;
- pre-scan file is cold;
- full declared span is processed;
- HOT content integrity is preserved;
- no OOM/oom_kill occurred;
- cgroup state is readable;
- direct arm satisfies no-fallback contract.

## Analysis

Produce:

- `trials.csv`;
- `block-pairs.csv`;
- `summary.json`.

Report medians and block-level paired differences only.

The pilot is not allowed to claim hypothesis support/non-support.

## Next step

Use observed block-level variance/effect distributions to run a Monte Carlo sizing study for a later confirmatory experiment.

Do not auto-launch confirmatory work.

## Attribution

This experiment was motivated by Strata's explicit use of direct I/O to keep semantically cold SSD-resident data out of host page-cache pressure.

No Strata implementation code is copied.

## Authority boundary

Pilot measurement only.
