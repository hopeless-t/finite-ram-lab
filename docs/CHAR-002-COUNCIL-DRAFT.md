# CHAR-002 — Mapping Identity Decomposition Council Draft

> **Status:** DRAFT / CHECKPOINTED BEFORE DESIGN FREEZE  
> **Scientific evidence:** NONE YET  
> **Experiment launched:** NO

## Why this document exists

HYP-002 falsified the tested final-recency explanation while leaving a strong stable A/B residency asymmetry.

The next research task is therefore to decompose lower-level causes of that asymmetry before resuming any semantic Value-of-Information calculation.

This document records the Council work completed before an interrupted bounce.

It is **not** a frozen experiment contract.

## Canonical incoming evidence

From HYP-002:

```text
mean(recent resident fraction - older resident fraction)
= -0.009035

exact one-sided sign-flip
p = 0.913574

cluster-bootstrap 95%
[-0.020865, +0.003025]
```

The final-recency hypothesis was not supported.

A strong identity-linked asymmetry remained:

```text
recent=A:
  mean recent-older = -0.16939

recent=B:
  mean recent-older = +0.15132
```

Exploratory reconstruction:

```text
mean B - A resident fraction = +0.1604
B > A in 94.5% of trials
```

Therefore the unresolved candidates include:

- mapping creation order;
- initial fault/touch order;
- virtual-address / VMA ordering;
- another stable per-mapping kernel state.

## Pseudo-Council progress before interruption

### Kernel / VM reviewer

Do not use semantic HOT identity as the primary axis.

CHAR-002 should characterize residency **before semantic reuse**.

The central question is which lower-level construction/layout factor predicts A/B residency under 160–162 MiB pressure.

### Memory-layout reviewer

Two separate anonymous mappings can confound mapping creation sequence with virtual-address placement.

A design that only reverses A/B creation order may therefore fail to separate:

```text
creation order
from
numeric virtual-address order
```

Record actual mapping base addresses.

Add a second layout family that uses one shared anonymous mapping split into two logical halves.

### Experimental-design reviewer

The draft design uses two complementary families.

#### Family S — Separate VMAs

Factors:

```text
MemoryHigh:
160 / 162 MiB

mapping creation order:
A→B / B→A

initial fault/touch order:
A→B / B→A
```

This produces:

```text
2 × 2 × 2 = 8 cells per runner block
```

Measure actual base virtual addresses so address ordering is observed rather than assumed.

#### Family H — Shared VMA halves

Create one 64 MiB anonymous mapping and split it into two 32 MiB logical regions.

Factors:

```text
MemoryHigh:
160 / 162 MiB

label orientation:
A=lower / B=upper
A=upper / B=lower

initial fault/touch order:
A→B / B→A
```

Again:

```text
2 × 2 × 2 = 8 cells per runner block
```

This family removes separate-VMA creation-order differences while preserving a lower-versus-upper virtual-address comparison.

### Statistics reviewer

Runner identity should remain the replication block.

Do not collapse the mechanism search into a single weighted score.

Candidate block-level outputs:

1. separate-VMA creation-order effect on residency;
2. separate-VMA initial-fault-order effect;
3. shared-VMA lower-versus-upper address effect;
4. shared-VMA initial-fault-order effect.

Candidate inference:

- exact sign-flip tests over runner-block contrasts;
- runner-cluster bootstrap intervals.

### Falsification reviewer

The current identity interpretation should be weakened if the asymmetry disappears when A/B labels are balanced.

A creation-order explanation should be weakened if the residency advantage does not follow first/second mapping creation.

A fault-order explanation should be weakened if residency does not follow first/second initial fault order.

A virtual-address explanation should be weakened if the shared-VMA lower/upper halves show no stable residency difference.

If creation order and actual numeric VMA ordering remain collinear in Family S, CHAR-002 must report that limitation rather than claiming separation.

### Reproducibility reviewer

A draft allocation discussed before interruption was:

```text
16 independent runner blocks

Family S:
8 cells / block

Family H:
8 cells / block

total:
16 cells / block
× 16 blocks
= 256 trials
```

This is **not frozen yet**.

### Monte Carlo reviewer

The draft Council was leaning toward **not using a design Monte Carlo** for this stage.

Reason:

- the scientifically relevant factorial cells can all be executed directly;
- the unresolved uncertainty is primarily **mechanism identity**, not a rare-event probability;
- factorial orthogonalization matters more here than simulated power under invented mechanism amplitudes.

This is still a draft methodological conclusion and must be re-confirmed in the next fresh bounce.

## Measurement candidates

For every trial, candidate direct measurements include:

- base virtual address of each region;
- mapping creation order;
- initial fault/touch order;
- A/B resident fraction immediately after pressure burst;
- memory.current;
- memory.swap.current;
- memory.stat reclaim/refault counters;
- memory.events;
- content-integrity checks;
- OOM checks.

No semantic memory hint or reclaim intervention should be introduced.

## What has NOT happened

As of this checkpoint:

- no CHAR-002 spec is frozen;
- no CHAR-002 implementation exists;
- no CHAR-002 workflow exists;
- no CHAR-002 GitHub Actions run has occurred;
- no CHAR-002 result exists.

## Next Council task

A fresh worker should rehydrate from this checkpoint and answer only:

> Is the two-family 16-block / 256-trial decomposition the smallest defensible design for separating creation order, initial fault order, and virtual-address position?

If yes, freeze the contract.

If no, revise it **before** implementation or data collection.

## Authority boundary

This draft does not establish the cause of the A/B residency asymmetry.

It records design reasoning only.
