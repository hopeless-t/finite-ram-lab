# STRATA-002-PILOT-v1 Result

> **Status:** PASS / PILOT ONLY
> **Run:** `36338522437`
> **Aggregate artifact:** `STRATA-002-PILOT-36338522437`
> **Artifact id:** `10938470859`
> **Artifact digest:** `sha256:bec214018ea7a71e948cdb13c76c5292613f2fc0dd16a1bb03929988c747149d`

## Validity

All frozen checks passed:

- 8 runner blocks;
- 32 trials;
- all arms once per block;
- all trials valid;
- file cold before every scan;
- advice support explicit;
- Linux NOREUSE semantics supported;
- O_DIRECT no fallback;
- content integrity preserved;
- no OOM.

Launch-commit ordinary CI also passed:

- run `36338522444`
- conclusion `success`

## Median outcomes

| Arm | high events | memory.current MiB | memory.peak MiB | file residency | cgroup file MiB | scan ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| buffered | 5.0 | 159.32 | 161.92 | 0.8646 | 83.00 | 86.36 |
| buffered_noreuse | 5.5 | 159.00 | 161.58 | 0.8542 | 82.01 | 59.96 |
| buffered_dontneed | 0.0 | 75.86 | 81.86 | 0.0000 | 0.00 | 82.42 |
| direct | 0.0 | 75.86 | 75.86 | 0.0000 | 0.05 | 89.62 |

HOT anonymous residency remained 1.0000 in every arm.

Median HOT-retouch latency stayed near 1.87–1.90 ms.

No swap was used.

## Paired pressure effect vs ordinary buffered

### buffered_dontneed

Across all 8 blocks:

`memory.events:high` difference:

`[-6, -5, -5, -5, -5, -5, -6, -6]`

Median:

`-5`

Paired `memory.current` difference median:

`-82.98 MiB`

Post-scan file-residency difference median:

`-0.8646`

Scan-time ratio median:

`1.027`

The block-level scan-time ratios were highly variable:

`[1.044, 1.010, 0.260, 2.969, 0.560, 1.465, 0.769, 2.025]`

Therefore the pilot strongly exposes a pressure-footprint mechanism but does not yet support a stable throughput claim.

### buffered_noreuse

Pressure outcomes were effectively unchanged from ordinary buffered I/O.

Median paired effects:

- high events: `0`
- memory.current: `0 MiB`
- post-scan file residency: `0`

In this short one-shot scan, NOREUSE did not reproduce the immediate footprint reduction produced by DONTNEED.

### direct

Pressure behavior closely matched buffered_dontneed:

- median high-events difference: `-5`
- median memory.current difference: `-83.35 MiB`
- median post-scan file-residency difference: `-0.8646`

This makes O_DIRECT a useful mechanism reference, but not a necessary implementation if DONTNEED can be validated.

## Interpretation

The strongest practical finding so far is:

> ordinary buffered reads followed by per-chunk POSIX_FADV_DONTNEED can, in this controlled Linux cgroup workload, reduce retained COLD file-cache pressure to approximately the same level as O_DIRECT while keeping ordinary buffered-read semantics.

This is exactly the shape desired for a personal-PC helper, but it remains a hosted-runner pilot.

## Why this matters for a personal PC

A helper can operate at the application boundary:

1. application declares a stream one-shot/COLD;
2. read normally through the page cache;
3. after an aligned chunk is consumed, issue DONTNEED for that completed range;
4. Linux remains responsible for global reclaim decisions.

This is materially less invasive than:

- global `drop_caches`;
- kernel tuning;
- forcing O_DIRECT everywhere.

It is also safer for mixed workloads because reusable data can remain ordinary cached data.

## Next scientific step

Run a confirmatory design study for `buffered_dontneed vs buffered`.

The confirmatory target should focus on:

- pressure-footprint efficacy;
- mechanism fidelity;
- a separately bounded latency-risk criterion.

NOREUSE should not advance to confirmatory testing from this pilot.

## Authority boundary

Pilot evidence only.

No production recommendation or automatic local-PC mutation is authorized.
