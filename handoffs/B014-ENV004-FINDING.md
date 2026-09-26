# Bounce Handoff

> **Bounce ID:** B014  
> **Status:** COMPLETE

## Objective

Read ENV-004 using the frozen capability classification and decide whether the instrument is usable.

## Evidence

- run: `36227867747`;
- 4 independent runner blocks;
- 8 total trials;
- all pageout calls succeeded;
- all proactive reclaim requests succeeded;
- all content checks passed;
- no OOM events.

## Frozen finding

ENV-004 is **SELECTIVE**.

After reclaim:

    target median residency = 0.0000
    target max residency    = 0.00488
    control median          = 1.0000
    control minimum         = 1.0000

Median target retouch was about 103.5 ms versus about 0.354 ms for the resident matched control.

## Authorized next step

A matched causal intervention experiment is now justified.

## Next recommended bounce

> Design the smallest randomized paired experiment that swaps which semantic region is selectively reclaimed while holding total memory and later workload constant.

Use Monte Carlo before freezing runner count/repeats if the transition-zone noise model makes design choice non-obvious.

## Authority boundary

Instrument capability is not evidence that a production coordinator or kernel change is useful.
