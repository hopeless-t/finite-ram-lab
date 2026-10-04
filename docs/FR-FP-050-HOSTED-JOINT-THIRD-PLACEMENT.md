# FR-FP-050 — Hosted physical third-placement validation

Status: **HOSTED PHYSICAL JOINT-PLACEMENT CANDIDATE**

Parent: **FR-FP-049**

## Why

FR-FP-049 disproved the HOLD-vs-semantic-optimum candidate restriction in the
joint model.

Fifteen of 35 contexts selected a third placement.

FR-FP-050 tests two high-margin representatives with real hosted tier
actuation.

## Context A — growth

    56 -> 72 MiB
    horizon = 50

Current:

    {0,1,2,3,7,8,9}

Migration-blind semantic optimum:

    {0,1,2,4,5,7,8,9}

Joint optimum:

    {0,1,2,3,6,7,8,9}

The joint policy promotes only state 6, a 16 MiB state.

## Context B — pressure shrink

    92 -> 44 MiB
    horizon = 20

Current placement exceeds the new capacity.

Semantic optimum:

    {1,3,7,8,9}

Joint optimum:

    {0,4,7,8,9}

The joint placement minimizes the physical move required while remaining within
44 MiB and keeping mandatory states WARM.

## Physical method

For every candidate:
- prepare a fresh ten-file fixture in the current placement;
- actuate only changed states;
- measure wall-clock migration cost;
- verify mincore WARM/COLD residency;
- verify exact target resident bytes.

Hybrid total:

    frozen synthetic service cost over H
      + observed hosted physical migration cost

The service component is not claimed physical.

## Qualification

Require the joint placement to beat:
- migration-blind semantic optimum in both contexts;
- HOLD where HOLD is capacity-feasible.

## Claim ceiling

**HOSTED_PHYSICAL_VALIDATION_OF_TWO_FP049_THIRD_PLACEMENT_CONTEXTS_ONLY**
