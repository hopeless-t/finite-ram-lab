# STRATA-001 Capability Contract

> **Status:** FROZEN / NOT YET EXECUTED
> **Inspired by:** https://github.com/Niko1221/Strata
> **Observed upstream revision:** `8117643ccc68e3d08f80d38e064333742d4474bb`

## Purpose

Before running a pressured-memory experiment, verify that the selected Linux runner can actually express the mechanism being studied.

STRATA-001 depends on a real distinction between:

- ordinary file access that participates in Linux page cache;
- direct I/O that does not intentionally populate that cache.

If that distinction is not observable on the selected runner/filesystem, the main experiment must not run there.

## Arms

Each arm receives its own freshly prepared 16 MiB file.

### MMAP

Map read-only and touch each page sequentially.

### BUFFERED_PREAD

Open normally and sequentially read through one fixed reusable 4 MiB buffer.

### DIRECT_PREAD

Open with `O_DIRECT` and sequentially read through one fixed reusable page-aligned 4 MiB buffer.

There is **no fallback** from DIRECT_PREAD to ordinary buffered I/O.

An `EINVAL`, unsupported filesystem, or alignment failure is a capability result, not permission to weaken the arm.

## File preparation

Each file is:

1. written completely;
2. fsync'd;
3. advised `POSIX_FADV_DONTNEED`;
4. measured for file-page residency before the arm runs.

The pre-scan cached fraction must be <= 0.10.

A trial with a materially warm file is invalid for this capability contract.

## File-page residency

The probe uses a read-only file mapping plus `mincore(2)` only to observe page-cache residency.

Creating the observation mapping must not itself be interpreted as reading the file data.

## PASS requirements

- all three arms consume exactly the expected byte count;
- DIRECT_PREAD genuinely opened/read with `O_DIRECT`;
- MMAP post-scan file residency >= 0.50;
- BUFFERED_PREAD post-scan file residency >= 0.50;
- DIRECT_PREAD post-scan file residency <= 0.10;
- no arm silently substitutes another I/O path.

## HOLD result

If the selected filesystem or hosted environment cannot satisfy direct-I/O alignment/support requirements, record:

`CAPABILITY_HOLD`

That is not evidence that page-cache bypass is ineffective.

## What this does not test

This probe does not test:

- anonymous-memory preservation;
- cgroup pressure;
- retouch latency;
- end-to-end application benefit;
- production workloads.

Those belong to the later pilot/confirmatory experiment.

## Attribution boundary

The experiment was motivated by Strata's explicit direct-I/O design.

The finite-ram-lab implementation is independent and does not copy Strata source code.

## Next stage after PASS

Run a bounded pilot under cgroup `memory.high` with a semantically HOT anonymous region and semantically COLD file scan.

Use the pilot only to estimate variance and choose a confirmatory design by Monte Carlo.
