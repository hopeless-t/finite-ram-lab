# B479 — Independent Runner-Block Factorial Replication v0.1

Status: **RUNNER-LEVEL BLOCKING / FACTOR REPLICATION**.

## 1. Why the experimental unit changes

B478 used fresh child processes inside one GitHub Actions job.

That isolates process-level state, but all children still share one hosted runner
VM.

The remaining q2 historical-vs-current shift may therefore be:

- a persistent temporal change;
- one runner-instance offset;
- a host/image/CPU effect;
- an interaction with the seed effect.

B479 promotes the GitHub Actions job itself to an experimental block.

## 2. Eight independent job blocks

The workflow launches eight matrix jobs.

Each block runs:

- q2 seed474 twice;
- q2 seed476 twice;
- q4 seed474 twice;
- q4 seed476 twice.

Total per block:

`8 fresh child processes`.

Total physical child observations:

`8 blocks x 8 = 64`.

Within each block, one condition order is followed by its reverse.

Across blocks, the four base orders are repeated twice.

## 3. Environment fingerprint

Each block records:

- runner name;
- GitHub image OS/version when available;
- kernel release;
- machine architecture;
- Python version;
- NumPy version;
- page size;
- CPU model;
- total visible memory.

These fields are diagnostic metadata, not proof that unrecorded host state is
identical.

## 4. Block-level effects

For every runner block:

### Seed effect

```text
seed_delta(q)
=
median_peak(q,476)
-
median_peak(q,474)
```

B478 predicts a negative seed effect for q2 and q4.

### Temporal / runner effect

```text
temporal_delta(q)
=
median_peak_current_block(q,474)
-
median_peak_historical_B474(q,474)
```

B478 predicts a positive temporal component for q2.

q4 serves as a control because B478 found no temporal q4 shift.

## 5. Confirmatory block tests

Four confirmatory tests are frozen:

1. q2 seed delta is negative;
2. q4 seed delta is negative;
3. q2 temporal delta is positive;
4. q4 temporal delta differs from zero in either direction.

The first three directions come from B478.

q4 temporal is two-sided because B478 treated it as a no-shift control.

Exact sign tests operate on independent runner-block deltas.

Family alpha:

`0.05`

Bonferroni per-test alpha:

`0.0125`

With eight nonzero blocks, a directional effect must be extremely consistent to
cross this threshold.

## 6. Why block-level replication matters

If seed effects repeat across runner blocks, the governor should condition on
workload identity instead of treating the effect as one-VM noise.

If q2 temporal shift also repeats across runner blocks, the current calibration
population has moved.

If q2 temporal deltas vary widely by block, runner-instance variance becomes a
first-class feature of the memory model.

## 7. Claim ceiling

**GITHUB_HOSTED_JOB_BLOCK_FACTORIAL_REPLICATION**

A matrix job is treated as an independent hosted-runner block for this bounded
experiment. Physical-host independence is not asserted.

## 8. Next

The result determines the next branch:

- persistent q2 temporal shift -> environment-aware recalibration / drift lane;
- runner-block heterogeneity -> hierarchical runner model;
- seed effects stable -> workload-conditioned governor;
- both -> hierarchical governor indexed by workload class and environment epoch.
