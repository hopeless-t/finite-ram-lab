# Bounce Handoff

> **Bounce ID:** B013  
> **Status:** COMPLETE / COMPUTE LAUNCHED

## Objective

Design and launch a bounded capability probe for selective proactive reclaim of a prepared anonymous target range.

## Pseudo-Council conclusion

- keep this as an instrument calibration, not a mechanism experiment;
- prepare only the target with `MADV_PAGEOUT`;
- request `memory.reclaim` with `swappiness=max` inside the experiment cgroup;
- measure target and matched-control residency directly with `mincore(2)`;
- preserve content-integrity and OOM checks;
- balance target identity A/B across independent hosted runners.

## Frozen probe

- 4 independent runner blocks;
- 2 target identities per block;
- 16 MiB target and 16 MiB matched control;
- proactive reclaim request: `16M swappiness=max`;
- MemoryHigh 256 MiB / MemoryMax 320 MiB;
- 8 total trials.

## Workflow

- commit: `d19f6cf4cad31f524393742d9ad46067f95d440b`
- run: `36227867747`

## Next recommended bounce

> Read back ENV-004, classify the instrument using only the frozen capability rules, and write the finding.

## Authority boundary

Launching ENV-004 is not evidence that selective reclaim works.
