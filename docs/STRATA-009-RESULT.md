# STRATA-009 Dataset Greater Than MemoryMax Result

> **Status:** PASS / DATASET-CAPACITY DECOUPLING SURVIVES MEMORYMAX CROSSING
> **Run:** `36440093666`
> **Launch commit:** `01e73be662613d164f62287f126ef002c8ff234c`
> **Aggregate artifact:** `STRATA-009-DATASET-GT-MEMORYMAX-36440093666`
> **Artifact id:** `10978190432`
> **Artifact digest:** `sha256:5128474d15bfed1071e145af5dc62eed1bd0af888323dbbf4272376450f1da4e`

## Validity

- 20 / 20 trials PASS
- 4 blocks x 5 bounded-policy arms
- cold dataset: 384 MiB
- MemoryMax: 320 MiB
- MemoryHigh: 160 MiB
- hot anon: 64 MiB
- Recorder: 98 records/trial
- buffered arm intentionally omitted
- no local-PC execution

Every trial completed without OOM or OOM kill.

## Boundary result

The total one-shot dataset is 1.2x MemoryMax and 2.4x MemoryHigh.

Observed response:

| arm | median high events | positive trials | peak MiB | non-hot floor MiB | advice calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| DONTNEED 64 | 0 | 0/4 | 142.426 | 13.301 | 6 |
| DONTNEED 72 | 0 | 0/4 | 150.299 | 13.078 | 6 |
| DONTNEED 80 | 0 | 0/4 | 158.428 | 13.207 | 5 |
| DONTNEED 88 | 30 | 4/4 | 159.680 | 13.422 | 5 |
| DONTNEED 96 | 70 | 4/4 | 159.680 | 13.428 | 4 |

Observed onset:

`80 MiB < K <= 88 MiB`

Transformed:

`144 MiB < K+hot <= 152 MiB`

Non-hot floor interval:

`[8,16) MiB`

All five DONTNEED cells had post-scan file residency 0.

## Capacity series

At the same MemoryHigh=160 MiB and hot anon=64 MiB:

- 96 MiB cold dataset: `80 < K <= 88`
- 192 MiB cold dataset: `80 < K <= 88`
- 384 MiB cold dataset: `80 < K <= 88`

Thus the observed knee remains unchanged while total dataset capacity scales 4x and crosses MemoryMax.

This supports:

`instantaneous RAM demand ~= effective live set + unreleased streaming interval`

rather than:

`instantaneous RAM demand ~= total dataset size`

for the tested one-shot streaming workload.

## Block replication

Each of 4/4 blocks independently showed:

- zero MemoryHigh events at release intervals 64 / 72 / 80 MiB;
- positive MemoryHigh events at 88 / 96 MiB;
- no OOM;
- no OOM kill;
- Recorder count exactly 98 per trial.

## Environment

All blocks:

- Ubuntu 26.04.1 LTS
- kernel `7.0.0-1012-azure`
- systemd `259 (259.5-0ubuntu3.4)`
- cgroup2fs
- runner image `20260920.143.1`
- X64

## Empirical bootstrap: 192 -> 384 MiB

The comparison uses observed DONTNEED trials only:

- n=20 at 192 MiB
- n=20 at 384 MiB
- metric: post-scan non-hot floor
- independent non-parametric bootstrap
- seed: `20260929`
- resamples: 200000

Observed medians:

- 192 MiB: 13.0546875 MiB
- 384 MiB: 13.296875 MiB
- shift: +0.2421875 MiB

95% bootstrap interval for median shift:

`[+0.023438, +0.376953] MiB`

Observed mean shift:

`+0.226172 MiB`

95% bootstrap interval:

`[+0.110352, +0.342188] MiB`

The floor therefore shows a small measurable sub-MiB shift while the 8 MiB knee remains unchanged.

## Observer caveat

The fine-grained post-scan floor is not yet a pure workload quantity.

`_file_residency()` maps the entire file and invokes `mincore` before post-scan `memory.current` is captured. Its own footprint can scale with the observed file and contaminate sub-MiB floor differences.

Therefore:

- the unchanged knee is accepted as robust evidence;
- the small floor-growth sequence is not yet accepted as a workload law;
- an observer-only footprint experiment is required before interpreting the +0.2421875 MiB-per-doubling pattern.

## Pseudo-Council convergence

- **Systems:** bounded streaming processed a dataset larger than MemoryMax without OOM.
- **Finite-RAM:** total dataset capacity is decoupled from the observed instantaneous knee under the tested release policy.
- **Statistics:** the knee replicates across all blocks and 96/192/384 MiB capacities.
- **Measurement:** sub-MiB floor growth may contain `mincore` observer cost and must be isolated.
- **Authority:** no automatic controller or deployment default follows.

Consensus:

**Promote dataset-capacity decoupling across the tested 96/192/384 MiB range. Do not promote the sub-MiB floor-growth pattern until observer footprint is measured.**

## Next research question

How much memory does the residency observer itself retain as target file size scales?

Measure observer-only deltas at 96 / 192 / 384 MiB without the streaming workload.

## Authority boundary

Hosted research only.
No local-PC execution.
No OSS default cadence or memory controller authorized.
