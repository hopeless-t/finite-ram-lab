# Bounce Handoff

> **Bounce ID:** B020  
> **Status:** COMPLETE

## Objective

Classify `MADV_COLD` using the frozen ENV-005 residency-bias criteria.

## Evidence

- run: `36228386627`;
- 8 runner blocks;
- 16 valid trials;
- all advice calls succeeded;
- median target residency = 1.0;
- median control residency = 1.0;
- median paired difference = 0.0;
- exact sign-flip p = 0.125.

## Frozen finding

`MADV_COLD` is **INEFFECTIVE for this workload** as a selective semantic-region steering instrument.

## Next recommended bounce

> Probe the next existing userspace mechanism: apply `MADV_PAGEOUT` to the not-soon-needed region before the same natural 164 MiB pressure burst, but do not call `memory.reclaim`.

The capability question is whether pageout preparation plus natural pressure produces selective target nonresidency while the matched unprepared region stays resident.

## Authority boundary

Do not generalize the negative result beyond this workload. Do not build a new coordination mechanism yet.
