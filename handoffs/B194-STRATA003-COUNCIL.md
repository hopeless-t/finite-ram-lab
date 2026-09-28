# Bounce Handoff

> **Bounce ID:** B194
> **Status:** COMPLETE / STRATA-003 RELEASE-CADENCE COUNCIL CONVERGED

## Question

How coarse can sliding DONTNEED become before transient memory pressure returns?

## Arms

- buffered
- DONTNEED every 4 MiB
- 8 MiB
- 16 MiB
- 32 MiB
- 96 MiB / end-of-stream only
- direct reference

## Pilot

- 8 blocks
- 56 trials
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- HOT anon 64 MiB
- COLD file 96 MiB
- read buffer 4 MiB

## New critical measurement

Sample cgroup memory.current internally after each 4 MiB read.

This separates transient pressure from final cache cleanup.

## Next action

Freeze STRATA-003-PILOT-v1.

## Authority boundary

Hosted research only.
