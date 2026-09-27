# Bounce Handoff

> **Bounce ID:** B174
> **Status:** COMPLETE / STRATA-002-PILOT-v1 FROZEN

## Frozen design

- 8 blocks
- 32 trials
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- HOT anon 64 MiB guardrail
- COLD file 96 MiB
- 4 MiB buffer

Arms:

- buffered
- buffered + NOREUSE
- buffered + sliding DONTNEED
- direct reference

## Primary outcomes

- MemoryHigh events during scan
- memory.current
- memory.peak
- file-cache residency

## Next action

Implement workload, analysis, regression tests, and bounded workflow.

## Authority boundary

Research only.
