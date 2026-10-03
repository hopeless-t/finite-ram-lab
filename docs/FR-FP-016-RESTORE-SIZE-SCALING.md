# FR-FP-016 — Warm-cold restore size scaling

Status: **HOSTED PHYSICAL SCALING CANDIDATE**

Parent: **FR-FP-015**

## Why

FR-FP-014 measured one 8 MiB point.

A Governor cannot safely assume the same restore ratio for every state size.

FR-FP-016 measures the restore surface at:

    4 MiB
    8 MiB
    16 MiB

with six paired WARM/COLD blocks per size.

## Tier preparation

WARM:

- anonymous state -> file;
- fsync;
- verify;
- source unmap;
- keep page cache resident.

COLD:

- same durable preparation;
- POSIX_FADV_DONTNEED;
- verify mincore nonresidency before restore.

Arm order alternates by block and size.

## Restore

Each file is restored into a fresh anonymous mmap through preadv.

Every restore must:

- read the full declared byte count;
- pass sentinel integrity.

## Model

For each tier, fit median restore read time to:

    latency_ns
      ~= intercept_ns
       + slope_ns_per_MiB * size_MiB

The inverse slope is reported as an effective transfer bandwidth.

The first qualification requires:

- WARM files physically resident before restore;
- COLD files nonresident before restore;
- COLD median slower than WARM at all three sizes;
- median latency increases with size for both tiers;
- R² > 0.95 for both three-point fits.

The fit is a hosted empirical model, not a storage-device specification.

## North-Star consequence

A state-tier decision can evolve from:

    one fixed restore penalty

to:

    restore_cost(state_bytes, tier)

This allows the warm/cold break-even frontier to adapt to variable state size.

## Claim ceiling

**HOSTED_LINUX_WARM_COLD_RESTORE_SIZE_SCALING_ONLY**
