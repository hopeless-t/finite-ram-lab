# STRATA-001 Capability Result

> **Status:** PASS
> **Run:** `36336116804`
> **Artifact:** `STRATA-001-CAPABILITY-36336116804`
> **Artifact id:** `10937625451`
> **Artifact digest:** `sha256:e70ed940fae955cd728794a1b60db4e08b07c25b40128fee6df1de5603226e32`

## Environment

- runner: GitHub-hosted Ubuntu 24.04
- filesystem: ext4
- mount point: `/`
- page size: 4096 bytes

## Result

All three files were cold before their scans.

| Arm | Pre-cache | Post-cache | Scan time |
| --- | ---: | ---: | ---: |
| MMAP | 0.0000 | 1.0000 | 15.657 ms |
| BUFFERED_PREAD | 0.0000 | 1.0000 | 7.303 ms |
| DIRECT_PREAD / O_DIRECT | 0.0000 | 0.0000 | 9.918 ms |

Each arm consumed exactly 16 MiB.

The direct arm:

- opened and read through `O_DIRECT`;
- did not fall back to buffered I/O;
- left the observed file-page residency at 0%;
- returned no I/O error.

## Interpretation

The capability prerequisite is satisfied on this runner/filesystem.

The mechanism distinction required by STRATA-001 is observable:

- mmap and ordinary buffered pread populate Linux page cache;
- O_DIRECT can read the same logical file span without materially populating page cache.

This result does **not** yet show a memory-management benefit.

At 16 MiB in this single capability run, direct pread was slower than buffered pread but faster than the page-touch mmap scan. These timing values are descriptive only and are not a performance comparison because the probe was not designed or replicated for timing inference.

## Next scientific question

Under a fixed cgroup memory budget, does avoiding page-cache population for a semantically COLD file preserve more of a semantically HOT anonymous region and reduce its subsequent reuse cost?

That question belongs to the bounded STRATA-001 pressure pilot.

## Attribution

STRATA-001 was inspired by Niko1221/Strata:

https://github.com/Niko1221/Strata

Observed upstream revision during design:

`8117643ccc68e3d08f80d38e064333742d4474bb`

The finite-ram-lab probe is independently implemented.
