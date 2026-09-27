# Bounce Handoff

> **Bounce ID:** B172
> **Status:** COMPLETE / STRATA-001 PILOT RECOVERED AND CANONICALIZED

## Result

The existing six successful physical block artifacts from run `36336994450` were recovered after collector-fix CI passed.

All 36 trials are valid.

## Primary pilot finding

HOT anonymous residency was 1.0000 in every arm, block, and tested pressure level.

DIRECT - BUFFERED HOT-residency paired difference:

- 160 MiB: six values all 0.0
- 168 MiB: six values all 0.0

No confirmatory sizing should be spent on this exact primary endpoint.

## Mechanism finding

DIRECT kept post-scan file residency at 0.0 and median cgroup memory.current near 75.86 MiB.

BUFFERED/MMAP retained roughly 84–92 MiB of file-cache memory and produced MemoryHigh events, but Linux still preserved the HOT anonymous region.

## Decision

Reframe before Monte Carlo.

Next Council should prioritize a practical buffered-stream cache-release mechanism and cross-process relevance rather than forcing a confirmatory HOT-residency study in a regime with zero observed headroom.

## Authority boundary

Pilot only.
