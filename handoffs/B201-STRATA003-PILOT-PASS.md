# Bounce Handoff

> **Bounce ID:** B201
> **Status:** COMPLETE / STRATA-003 PILOT PASS CANONICALIZED

## Key result

All 56 trials passed.

DONTNEED cadences 4 / 8 / 16 / 32 MiB:

- median MemoryHigh events = 0.

96 MiB / end-of-stream:

- median MemoryHigh events = 6;
- max scan memory approximately buffered baseline;
- final memory still drops to ~76 MiB.

## Interpretation

Final cache cleanup is not enough.

The helper must release consumed COLD ranges while streaming.

Current cadence knee bracket:

`32 MiB < knee <= 96 MiB`

## Product consequence

32 MiB used only 3 advice calls per 96 MiB stream, an 8x call-count reduction vs 4 MiB, while preserving complete observed pressure-event suppression.

Do not freeze 32 MiB as default yet.

## Next action

Converge a small targeted knee-refinement study between 32 and 96 MiB.

## Authority boundary

Hosted research only.
