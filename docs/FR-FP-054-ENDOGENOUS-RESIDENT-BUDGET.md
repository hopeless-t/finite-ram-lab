# FR-FP-054 — Endogenous resident usage

Status: **SYNTHETIC RESIDENT-RENT FRONTIER CANDIDATE**

Parent: **FR-FP-053**

## Why

The multi-state Governor already decides which states deserve WARM residency.

But the phase capacity has still been treated mainly as something to fill up to
the semantic/migration optimum.

The North Star is stricter:

> keep only the resident bytes whose semantic value justifies their byte-time
> cost.

FR-FP-054 keeps the existing phase capacities as hard safety maxima, but makes
actual WARM usage endogenous.

## Objective

For each online phase, minimize exactly:

    H * ColdPenalty(S)
      + MigrationCost(current -> S)
      + H * lambda * WarmMiB(S)

subject to:

    WarmMiB(S) <= hard capacity

and the existing mandatory-WARM constraints.

Where:

- H is the phase validity horizon;
- lambda is an explicit memory shadow price in ms per MiB per round.

The migration model uses the qualified FP053 current-run direction scales.

## Important distinction

The hard capacity is not removed.

It remains an external maximum.

The new behavior is:

    capacity is a ceiling
    not a target

The Governor may deliberately leave memory unused when resident byte-time costs
more than the semantic service it saves.

## Qualification

Sweep a frozen lambda grid.

For every lambda and every phase:

- dynamic programming must exactly match exhaustive subset search;
- the hard capacity must never be exceeded.

Across lambda:

- lambda=0 must recover the FP053 path;
- aggregate resident MiB-round must be nonincreasing;
- each phase's resident MiB must be nonincreasing;
- positive lambda must be able to leave available capacity unused.

## North-Star meaning

This moves the control variable from:

    which states fit in the supplied WARM budget?

to:

    how many resident bytes are worth paying for right now, and which bytes are
    they?

That is a direct resident-byte-time formulation of Finite RAM.

## Claim ceiling

**SYNTHETIC_RESIDENT_RENT_FRONTIER_ON_FP051_PHASES_WITH_FP053_CURRENT_RUN_MIGRATION_SCALES_ONLY**
