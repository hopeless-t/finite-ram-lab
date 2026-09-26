# Bounce Handoff

> **Bounce ID:** B021  
> **Status:** COMPLETE / COMPUTE LAUNCHED

## Objective

Test whether 16 MiB `MADV_PAGEOUT` preparation plus natural 164 MiB pressure creates selective target nonresidency without explicit proactive reclaim.

## Frozen probe

- 8 runner blocks;
- target A/B balanced within every block;
- two 32 MiB regions;
- only first 16 MiB of selected target receives PAGEOUT;
- 96 MiB burst;
- MemoryHigh 164 MiB / MemoryMax 320 MiB;
- no `memory.reclaim` call.

## Workflow

- run: `36228551661`
- commit: `6ead4840124e4b26d77694ebdb9bf204b1cb7243`

## Next recommended bounce

> Classify the stronger existing mechanism using the frozen residency-bias rule.

## Authority boundary

ENV-006 is still capability evidence, not a performance-benefit experiment.
