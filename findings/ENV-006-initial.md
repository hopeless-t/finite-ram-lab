# ENV-006 Initial Finding

> **Status:** EFFECTIVE CAPABILITY  
> **Run:** 36228551661

## Question

Does `MADV_PAGEOUT` preparation of a 16 MiB semantic subrange make that subrange preferentially lose residency when the same natural 164 MiB pressure burst arrives, without explicit `memory.reclaim`?

## Execution

All frozen execution checks passed:

- 8 independent runner blocks;
- 16 total trials;
- target A/B balanced in each block;
- all PAGEOUT calls succeeded;
- all contents remained intact;
- no OOM events.

## Result

Immediately after PAGEOUT but before the burst:

    median target resident fraction = 1.000

This reproduces ENV-003's swap-backed-but-still-resident state.

After the natural pressure burst:

    median prepared target fraction = 0.62183
    median unprepared control        = 1.00000
    median target-control difference = -0.37817

The target-control difference was extremely stable:

    min = -0.37842
    max = -0.37817

Exact block-level sign-flip inference:

    observed mean difference = -0.37825
    exact two-sided p = 0.0078125

Swap:

    median swap growth after PAGEOUT = 16.0 MiB
    median swap growth after burst   = 16.0 MiB

## Classification

    EFFECTIVE

## Interpretation

`MADV_PAGEOUT` alone did not make the range nonresident before pressure, but it created a prepared state that the subsequent natural memcg pressure reclaimed preferentially.

The matched unprepared subrange remained fully resident.

This is materially different from ENV-005:

    MADV_COLD + natural pressure     -> no usable residency bias
    MADV_PAGEOUT + natural pressure  -> strong replicated residency bias

## Research consequence

A performance experiment using application knowledge is now justified with an **existing Linux interface**.

The minimal next test should compare:

- correct semantic preparation: PAGEOUT the not-soon-needed region;
- wrong semantic preparation: PAGEOUT the soon-needed region;
- no semantic preparation.

All arms should then undergo the same natural transition-zone pressure and reuse the same HOT region.

The PAGEOUT call cost must be recorded so later analysis can distinguish next-use benefit from total intervention cost.

## Authority boundary

ENV-006 establishes steering capability, not net performance benefit.

It does not establish that applications should generally call PAGEOUT or that a new coordination plane is needed.
