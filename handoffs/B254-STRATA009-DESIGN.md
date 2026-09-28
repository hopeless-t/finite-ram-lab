# Bounce Handoff

> **Bounce ID:** B254
> **Status:** COMPLETE / STRATA-009 >MEMORYMAX DESIGN FROZEN

## Parent

STRATA-008 PASS:

- cold 96 -> 192 MiB did not move the 80–88 MiB knee;
- floor movement remained sub-MiB;
- empirical bootstrap recorded.

## STRATA-009 frozen design

- cold file: 384 MiB
- MemoryMax: 320 MiB
- MemoryHigh: 160 MiB
- hot anon: 64 MiB
- Ubuntu 26.04 / Python 3.12
- DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 20 trials
- REC-001 98 records/trial

Buffered is intentionally omitted because an expected OOM/unbounded control needs a separate evidence-preserving harness contract.

## Next action

Implement STRATA-009 only. Do not launch in the implementation bounce.

## Authority

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
