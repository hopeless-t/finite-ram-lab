# FR-FP-015 — Warm-cold break-even frontier

Status: **ANALYTIC FRONTIER CANDIDATE**

Parent: **FR-FP-014**

Evidence: **PR #133**

## Why

FR-FP-013 measured the residency benefit of moving durable file state from WARM
page cache to COLD nonresident storage.

FR-FP-014 measured the restore penalty.

The next temptation is to invent one score and declare WARM or COLD the winner.

FR-FP-015 refuses to hide that value judgment.

Instead it derives the break-even frontier in terms of two explicit task
variables:

- probability that the state will be reused;
- shadow price of retaining one MiB resident.

## Measured inputs

Hosted 8 MiB state:

WARM restore median:

    847,494 ns

COLD restore median:

    3,102,932.5 ns

Restore penalty:

    2,255,438.5 ns

Physical page-cache residency difference before restore:

    8 MiB

## Expected incremental cost

Let:

    p = probability the state is restored
    lambda = cost of one resident MiB in ns-equivalent units
    DeltaL = Lcold - Lwarm
    DeltaM = Mwarm - Mcold

Then:

    WARM cost = lambda * Mwarm + p * Lwarm
    COLD cost = lambda * Mcold + p * Lcold

COLD is cheaper when:

    lambda * DeltaM > p * DeltaL

Therefore the break-even memory shadow price is:

    lambda_star(p)
      = p * DeltaL / DeltaM

For the frozen hosted pilot:

    lambda_star(p)
      = p * 281.9298125 microseconds / MiB

## Examples, not recommendations

At reuse probability 5%:

    break-even ~14.10 us/MiB

At reuse probability 10%:

    break-even ~28.19 us/MiB

At reuse probability 50%:

    break-even ~140.96 us/MiB

At reuse probability 100%:

    break-even ~281.93 us/MiB

These do not define the correct memory price.

They expose what the task contract must value before a tier decision can be
made.

## Why this matters

A high-reuse state can rationally stay WARM even when COLD saves memory.

A low-reuse state can rationally move COLD at the same memory pressure.

Thus a future Governor needs:

    state reuse probability
    memory pressure / shadow price
    restore-cost surface

not merely LRU age or current RSS.

## No hidden utility

This experiment does not assign a default lambda.

That belongs to an application or resource contract.

The research output is the frontier, not a universal winner.

## Claim ceiling

**ANALYTIC_BREAK_EVEN_FRONTIER_FROM_SINGLE_HOSTED_RESTORE_PILOT_ONLY**
