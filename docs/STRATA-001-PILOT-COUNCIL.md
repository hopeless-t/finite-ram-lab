# STRATA-001 Pressure Pilot Council

> **Status:** COUNCIL CONVERGED / PILOT AUTHORIZED FOR FREEZE
> **Inspiration:** https://github.com/Niko1221/Strata

## Inputs

STRATA-001 capability PASS established on GitHub-hosted Ubuntu 24.04 / ext4:

- MMAP: file residency 0% -> 100%
- BUFFERED_PREAD: 0% -> 100%
- DIRECT_PREAD / O_DIRECT: 0% -> 0%

The mechanism can therefore be expressed on the selected runner.

Finite RAM Lab already has a known semantic-region pressure regime using:

- 64 MiB semantically HOT anonymous memory;
- 96 MiB competing memory;
- MemoryHigh around 160–168 MiB.

## Question

When the 96 MiB competing working set is a semantically COLD file rather than anonymous burst memory, does page-cache bypass preserve the 64 MiB semantically HOT anonymous region under the same nominal MemoryHigh transition region?

## Council seats

### Causal seat

Primary contrast:

`BUFFERED_PREAD vs DIRECT_PREAD`

Both paths:

- open the same file read-only;
- scan the same byte range in the same order;
- use the same fixed reusable 4 MiB userspace buffer;
- use preadv-style reads.

The intended mechanism difference is page-cache participation.

MMAP is retained as a secondary architectural arm because it is a common file-backed access path and was part of the Strata inspiration, but its scan-time cost is not directly comparable to pread because it touches pages rather than copying the entire file through a userspace read buffer.

### Memory-pressure seat

Reuse the previously informative nominal pressure levels:

- 160 MiB;
- 168 MiB.

This is a pilot, not a confirmatory claim that the old transition must transfer unchanged from anonymous pressure to file-backed pressure.

MemoryMax remains 320 MiB.

### Semantic seat

The anonymous region is HOT by contract:

- allocate 64 MiB;
- fault/touch every page;
- do not access it during the file scan;
- immediately reuse every page after the scan.

The file is COLD by contract:

- scan 96 MiB once;
- do not reuse its contents during the measured interval.

This creates a controlled semantic asymmetry.

### Contamination seat

Before each trial:

1. fsync the file after preparation;
2. issue POSIX_FADV_DONTNEED;
3. verify observed file residency <= 10%.

A warm file invalidates the trial.

Use one per-runner file reused across sequential trials only after a fresh DONTNEED/cold check.

### Measurement seat

Immediately after file scan and before HOT reuse:

Primary:

- HOT anonymous resident fraction via mincore;
- cgroup `memory.stat anon`;
- cgroup `memory.stat file`;
- scanned-file resident fraction.

During HOT reuse:

- HOT retouch latency;
- pswpin;
- workingset_refault_anon;
- pgmajfault;
- pgfault;
- pgscan;
- pgsteal.

End-to-end/descriptive:

- file scan elapsed;
- scan + HOT retouch total work;
- cgroup memory.current / swap.current;
- no OOM.

### Design seat

Pilot only:

- 6 independent hosted-runner blocks;
- 2 MemoryHigh levels;
- 3 arms;
- exactly one trial per cell per block;
- 36 trials total;
- deterministic shuffled order within each block.

This is deliberately small.

The pilot estimates:

- effect direction;
- block-to-block variance;
- mechanism fidelity;
- whether a confirmatory experiment is worth sizing.

It does not accept/reject the scientific hypothesis.

### Statistics seat

Report per arm × pressure:

- median HOT resident fraction;
- median HOT retouch latency;
- median file-cache residency;
- median cgroup anon/file bytes;
- raw block-level paired differences.

Primary pilot effect surface:

`DIRECT_PREAD - BUFFERED_PREAD`

for HOT resident fraction.

Secondary:

- log HOT-retouch ratio;
- total-work ratio.

No p-value gate and no production claim in the pilot.

Monte Carlo sizing comes **after** pilot evidence exists.

### Reliability seat

Each runner block is one GitHub Actions job.

Do not automatically launch confirmatory work from pilot completion.

## Decision

Proceed with **STRATA-001-PILOT-v1**:

- HOT anonymous = 64 MiB;
- COLD file = 96 MiB;
- buffer = 4 MiB;
- MemoryHigh = 160 / 168 MiB;
- MemoryMax = 320 MiB;
- arms = mmap / buffered_pread / direct_pread;
- 6 blocks;
- 36 trials.

## Stop conditions

Stop before inference if:

- O_DIRECT fails or silently falls back;
- pre-scan file residency > 10%;
- content integrity fails;
- any OOM occurs;
- arms do not read/touch the declared 96 MiB span;
- cgroup accounting is unavailable.

## Attribution boundary

The experiment remains explicitly inspired by Strata's direct-I/O tiering choice.

No Strata source code is copied.

## Authority boundary

Pilot measurement only.
No generalized direct-I/O recommendation, kernel change, or deployment is authorized.
