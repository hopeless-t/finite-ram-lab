# STRATA-007 Cross-Image Portability Result

> **Status:** PASS / CROSS-IMAGE PORTABILITY SUPPORTED AT CURRENT RESOLUTION
> **Run:** `36435758885`
> **Launch commit:** `615cc9957d4f7e49cc60a7d799431ba149d6f22b`
> **Aggregate artifact:** `STRATA-007-CROSS-IMAGE-36435758885`
> **Artifact id:** `10975842099`
> **Artifact digest:** `sha256:1f677697ec810dd1f25dee0c7657044d55a52dee3874806579266bbae2370eb4`

## Validity

The Ubuntu 26.04 hosted study completed successfully.

- expected trials: 24
- aggregate trial count: 24
- execution status: PASS
- 4 runner blocks x 6 arms
- all block jobs succeeded
- no local-PC execution

All four blocks independently reproduced the same onset bracket.

## Executed substrate receipt

Each block reported:

- OS: Ubuntu 26.04.1 LTS
- kernel: `7.0.0-1012-azure`
- runner image OS: `ubuntu26`
- runner image version: `20260920.143.1`
- architecture: X64
- cgroup filesystem: `cgroup2fs`

The `systemd_version` field was blank in all four environment receipts because the workflow queried `systemd --version`.

The experiment still executed successfully through `systemd-run`, so this is an environment-receipt gap rather than a scientific trial failure. Do not claim an observed systemd-version difference from this run.

Future environment receipts should query the executable actually used by the harness, e.g. `systemd-run --version`.

## Response surface on Ubuntu 26.04

| arm | median high events | positive trials | median peak MiB | median non-hot floor MiB |
| --- | ---: | ---: | ---: | ---: |
| buffered | 6 | 4/4 | 159.10 | 95.22 |
| DONTNEED 64 | 0 | 0/4 | 142.81 | 12.81 |
| DONTNEED 72 | 0 | 0/4 | 150.80 | 12.93 |
| DONTNEED 80 | 0 | 0/4 | 158.81 | 12.81 |
| DONTNEED 88 | 3 | 4/4 | 158.94 | 12.94 |
| DONTNEED 96 | 6 | 4/4 | 159.08 | 13.05 |

Observed onset:

`80 MiB < K <= 88 MiB`

Transformed:

`144 MiB < K + hot <= 152 MiB`

Effective-live-set interval:

`[72, 80) MiB`

Non-hot floor interval:

`[8, 16) MiB`

Across all 20 DONTNEED trials, the measured post-scan non-hot floor had:

- median: `12.8125 MiB`
- observed range: approximately `12.805–13.313 MiB`

## Cross-image comparison

Ubuntu 24.04 STRATA-004 anchor:

`80 MiB < K <= 88 MiB`

Ubuntu 26.04 STRATA-007:

`80 MiB < K <= 88 MiB`

Both therefore map to:

`144 MiB < K + hot <= 152 MiB`

at MemoryHigh=160 MiB and hot anon=64 MiB.

The coarse interval result is unchanged across the two hosted Ubuntu image families.

The measured non-hot floor is not exactly identical. The prior Ubuntu 24.04 STRATA-004 median post-scan result implies roughly 11.9 MiB above the 64 MiB hot allocation, while Ubuntu 26.04 is roughly 12.8 MiB. This small shift is well inside the current 8 MiB cadence-grid resolution and does not move the observed knee bracket.

## Interpretation

The leading tested mechanism now survives three independent axes:

1. MemoryHigh changes: STRATA-005.
2. Hot/live-set changes: STRATA-006.
3. Hosted Ubuntu image/kernel changes: STRATA-007.

At the current measurement resolution, the consistent description is:

`pressure onset when release_interval + effective_live_set approaches MemoryHigh`

or:

`K ~= MemoryHigh - effective_live_set`

The exact substrate overhead is not universal and should be measured rather than hard-coded.

## Pseudo-Council convergence

- **Systems:** accept cross-image directional replication at the current 8 MiB grid resolution.
- **Causal inference:** the image/kernel axis changed while workload and pressure variables remained frozen.
- **Statistics:** four block replications are consistent, but only two hosted image families have been measured.
- **Recorder:** environment receipt has a concrete systemd-version gap; repair future receipts without retroactively changing this result.
- **OSS portability:** do not convert the observed non-hot floor into a constant or default.
- **Authority:** observation does not grant deployment or controller authority.

Consensus:

**Promote effective-live-set headroom to the leading portable mechanism candidate across the tested GitHub-hosted Ubuntu images. Next test whether total cold-data volume changes the bounded resident response.**

## Monte Carlo

Deferred.

Cross-image data now exists, but there are still only two substrate families and their onset intervals are identical at the current grid resolution. A substrate-offset probability distribution would remain weakly identified.

## Next research question

If the total one-shot cold dataset is doubled while MemoryHigh, hot live set, release cadence, and substrate are fixed, does the onset bracket and retained floor remain bounded?

This directly tests whether total dataset capacity is decoupled from instantaneous memory demand.

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default cadence or memory controller authorized.
