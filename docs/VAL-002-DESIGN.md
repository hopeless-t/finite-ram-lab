# VAL-002 Design Council — Observer-Effect Validation

> **Status:** FROZEN DESIGN

## Bounce objective

Determine whether the pre-retouch `mincore(2)` observation used by OBS-002 materially changes the transition-zone workload dynamics.

Repository state takes precedence over the older handoff recommendation to jump directly to causal intervention.

The latest OBS-002 finding explicitly requires observer-effect validation first.

## Pseudo-Council

### Measurement reviewer

OBS-002 changed two things relative to VAL-001:

1. allocation moved from Python `bytearray` to anonymous `mmap`;
2. residency observation added `mincore(2)`.

The endpoint controls reproduced, but the 164 MiB tail changed. The observer itself must be isolated.

### Kernel / VM reviewer

Use the existing `region_workload` implementation because it already supports:

```text
--mincore-mode full
--mincore-mode none
```

No new memory advice or control API is allowed.

### Statistician

Runner identity is a blocking factor.

Within every independent runner block, randomize both modes at the same `MemoryHigh` levels.

The primary estimand is the mode effect on log `HOTSET_RETOUCH` latency at 164 MiB.

Do not rely on a normal-error assumption.

Use blocked permutation and cluster bootstrap over runner blocks.

### Falsification reviewer

Observer effect remains a serious concern if `mincore=full` versus `none` materially changes any of:

- retouch latency distribution;
- swap-in / major-fault behavior;
- reclaim / pressure counters;
- probability of entering the slow transition branch.

### Reproducibility reviewer

Preserve 160 MiB and 168 MiB endpoint controls for both modes so the experiment can detect gross mode-dependent regime changes.

### Authority reviewer

Even if the observer effect is small, VAL-002 does not prove the Region Residency hypothesis.

It only determines whether OBS-002's measurement method is usable for the next causal experiment.

## Frozen design

Independent runner blocks:

```text
8
```

Within each runner block:

```text
160 MiB:
  mincore full × 1
  mincore none × 1

164 MiB:
  mincore full × 4
  mincore none × 4

168 MiB:
  mincore full × 1
  mincore none × 1
```

Total:

```text
12 trials / block × 8 blocks = 96 trials
```

Execution order is deterministically shuffled independently per block.

## Primary analysis

At 164 MiB:

```text
predictor: mincore mode (full vs none)
outcome: log(HOTSET_RETOUCH latency)
blocking unit: hosted runner
```

Report:

- block-level median latency by mode;
- full/none geometric-median ratio;
- within-block permutation distribution;
- cluster-bootstrap interval over whole runner blocks.

## Secondary analysis

Compare mode effects on:

- retouch `pswpin`;
- retouch major faults;
- `memory.high` events;
- `pgscan` / `pgsteal`;
- PSI totals;
- descriptive slow-branch frequency.

The previously used 50 ms transition-zone marker may be reported descriptively, but it is **not** a scientific acceptance threshold.

## Decision rule

Do not pre-declare “observer cleared” from a p-value.

After execution, a fresh pseudo-Council must inspect:

1. magnitude of the mode effect;
2. uncertainty interval;
3. whether pressure counters move in the same direction;
4. whether endpoint controls remain stable;
5. whether any mode effect is large enough to threaten the OBS-002 residency/latency interpretation.

## Prohibited in VAL-002

- `madvise`;
- `mlock`;
- pageout intervention;
- application memory hints;
- coordination agent;
- kernel changes.

VAL-002 is validation of the measuring instrument only.
