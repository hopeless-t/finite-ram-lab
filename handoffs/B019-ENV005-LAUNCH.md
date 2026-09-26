# Bounce Handoff

> **Bounce ID:** B019  
> **Status:** COMPLETE / COMPUTE LAUNCHED

## Objective

Test whether the smallest existing Linux semantic hint, `MADV_COLD`, measurably biases natural transition-zone reclaim toward the hinted region.

## Pseudo-Council conclusion

- capability first, performance claim later;
- no explicit `MADV_PAGEOUT` or `memory.reclaim` in ENV-005;
- two equal 32 MiB regions plus 96 MiB burst at MemoryHigh 164 MiB;
- balance target identity A/B in every runner block;
- direct paired residency comparison after the burst;
- exact 2^8 block sign-flip inference.

## Workflow

- run: `36228386627`
- commit: `9404113045bf38afb0348d8bf92218855b555a17`

## Next recommended bounce

> Classify MADV_COLD as EFFECTIVE / PARTIAL / INEFFECTIVE / UNAVAILABLE using the frozen residency-bias rules.

## Authority boundary

ENV-005 is capability evidence only. It does not test user-visible performance benefit.
