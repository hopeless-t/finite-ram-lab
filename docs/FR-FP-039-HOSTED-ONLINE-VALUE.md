# FR-FP-039 — Hosted physical online state-value reallocation

Status: **HOSTED PHYSICAL ONLINE-VALUE CANDIDATE**

Parent: **FR-FP-038**

## Question

FR-FP-038 qualified the shadow rule:

    new reuse evidence
      -> recompute state values
      -> recompute optimal WARM set
      -> actuate only the symmetric difference

One phase updated reuse evidence but left the optimal WARM set unchanged.

FR-FP-039 asks whether the same rule survives real page-cache actuation.

## Physical fixture

Ten durable 8 MiB files.

Shared WARM capacity:

    5 slots = 40 MiB

The target WARM sets are imported directly from the qualified FR-FP-038
shadow panel.

No new allocation law is introduced here.

## Actuation

Initial placement is materialized physically.

For each later evidence phase:

    changed = old WARM set XOR new WARM set

Only changed states receive:

- PREFETCH when moving COLD -> WARM;
- POSIX_FADV_DONTNEED when moving WARM -> COLD.

Unchanged states receive no tier action.

## Decision-irrelevant evidence phase

FR-FP-038 phase 3 -> 4 changes confidence values but not the optimal WARM set.

Required physical behavior:

    changed set = empty
    actuation count = 0
    before snapshot == after snapshot

This is a third decision plane for the pruning rule:

1. reuse monitoring;
2. calibration measurement;
3. multi-state physical placement.

## Qualification

Require:

- all physical WARM sets match the shadow targets;
- every phase remains at 40 MiB resident;
- WARM files are resident and COLD files nonresident;
- physical action count equals shadow minimal-delta count;
- at least one evidence update executes zero physical actions;
- every zero-action update preserves the full physical snapshot.

## Claim ceiling

**HOSTED_PHYSICAL_FIVE_PHASE_ONLINE_VALUE_REALLOCATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY**
