# STRATA-008 Cold-Capacity Invariance Result

> **Status:** PASS / BOUNDED-WORKING-SET SUPPORTED
> **Run:** `36437651740`
> **Launch commit:** `1843e566c8cf6e18322861cd6c7ee51b28cccc30`
> **Aggregate artifact:** `STRATA-008-COLD-CAPACITY-36437651740`
> **Artifact id:** `10976142662`
> **Artifact digest:** `sha256:8fbdf646686efe6923afd57e78c859b79ceeda9f2124b2c6fd6023de88909186`

## Validity

The Ubuntu 26.04 doubled-capacity study completed successfully.

- expected trials: 24
- aggregate trial count: 24
- execution status: PASS
- 4 runner blocks x 6 arms
- all block jobs succeeded
- Recorder density: 50 records/trial
- no local-PC execution

All four blocks independently reproduced the same onset bracket.

## Frozen comparison

Historical anchor from STRATA-007:

- cold file: 96 MiB
- `80 MiB < K <= 88 MiB`
- `144 MiB < K+hot <= 152 MiB`
- DONTNEED non-hot floor median: 12.8125 MiB

STRATA-008 changed only the one-shot cold-file capacity to 192 MiB.

## 192 MiB response surface

| arm | median high events | positive trials | median peak MiB | non-hot floor MiB | advice calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| buffered | 54 | 4/4 | 159.217 | 95.338 | 0 |
| DONTNEED 64 | 0 | 0/4 | 142.803 | 12.930 | 3 |
| DONTNEED 72 | 0 | 0/4 | 150.807 | 13.055 | 3 |
| DONTNEED 80 | 0 | 0/4 | 158.928 | 13.199 | 3 |
| DONTNEED 88 | 7 | 4/4 | 159.064 | 13.047 | 3 |
| DONTNEED 96 | 14 | 4/4 | 159.090 | 13.061 | 2 |

Observed onset:

`80 MiB < K <= 88 MiB`

Transformed:

`144 MiB < K+hot <= 152 MiB`

Effective floor:

`[72, 80) MiB`

Non-hot floor:

`[8, 16) MiB`

Thus doubling total cold capacity did not move the observed knee at the 8 MiB cadence-grid resolution.

## Total work versus instantaneous demand

The logical scan span doubled from 96 MiB to 192 MiB.

The DONTNEED advice-call count increased mechanically:

- 64 MiB cadence: 2 -> 3 calls
- 72 MiB cadence: 2 -> 3 calls
- 80 MiB cadence: 2 -> 3 calls
- 88 MiB cadence: 2 -> 3 calls
- 96 MiB cadence: 1 -> 2 calls

The amount of total work therefore increased, while the onset bracket and retained DONTNEED floor remained bounded.

This is direct support for separating:

`total dataset capacity`

from:

`instantaneous resident-memory demand`

for this one-shot streaming workload.

## Block replication

Each of 4/4 blocks showed:

- zero MemoryHigh events at 64 / 72 / 80 MiB release cadence;
- positive MemoryHigh events at 88 / 96 MiB cadence;
- therefore the same `80 < K <= 88` bracket.

## Environment receipt repair

All four blocks successfully recorded:

- Ubuntu 26.04.1 LTS
- kernel `7.0.0-1012-azure`
- systemd `259 (259.5-0ubuntu3.4)` via `systemd-run --version`
- cgroup2fs
- runner image `20260920.143.1`
- X64

The STRATA-007 environment-receipt defect is therefore repaired for future studies.

## Empirical bootstrap robustness check

Unlike earlier Monte Carlo proposals, this check uses only observed trial samples and does not invent a threshold-jitter distribution.

Input:

- 20 DONTNEED trials from the 96 MiB STRATA-007 study;
- 20 DONTNEED trials from the 192 MiB STRATA-008 study;
- statistic: post-scan non-hot resident floor;
- non-parametric independent bootstrap;
- deterministic seed: `20260928`;
- resamples: `200000`.

Observed:

- 96 MiB median: 12.8125 MiB
- 192 MiB median: 13.0546875 MiB
- median shift: +0.2421875 MiB
- bootstrap 95% interval for median shift: approximately `[-0.001953, +0.250000] MiB`

For the mean:

- observed mean shift: +0.133984375 MiB
- bootstrap 95% interval: approximately `[+0.034766, +0.231641] MiB`

Interpretation:

There may be a small sub-MiB capacity-associated offset in the retained floor, but it is far smaller than the 8 MiB onset-grid resolution and does not move the observed knee.

Do not claim exact equality of floors. Claim bounded, sub-MiB movement at the measured capacities.

## Pseudo-Council convergence

- **Systems:** total streamed capacity doubled while the DONTNEED knee stayed fixed.
- **Finite-RAM:** instantaneous demand is governed by live state plus unreleased interval, not by the full one-shot dataset size under the tested policy.
- **Statistics:** bootstrap supports a small possible floor shift but rejects any large movement in the observed sample regime.
- **Measurement:** timing remains secondary; more bytes naturally mean more work.
- **Portability:** this is still a specific Linux/cgroup/page-cache workload; do not generalize to arbitrary applications.
- **Authority:** no controller/default follows from the result.

Consensus:

**Promote bounded-working-set decoupling from total one-shot cold capacity to a supported mechanism on the tested hosted substrate. Next cross the configured MemoryMax with the dataset while preserving the same streaming policy.**

## Next research question

Can a one-shot cold dataset larger than the cgroup MemoryMax still preserve the same bounded instantaneous-memory response under DONTNEED?

A 384 MiB cold file is a high-information next point:

- 4x the original 96 MiB dataset;
- 2x STRATA-008;
- greater than MemoryMax=320 MiB;
- same MemoryHigh=160 MiB and hot=64 MiB.

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default cadence or memory controller authorized.
