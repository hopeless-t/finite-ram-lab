# Bounce Handoff

> **Bounce ID:** B161
> **Status:** COMPLETE / STRATA-001-PILOT-v1 FROZEN

## Frozen

- `specs/STRATA-001-PILOT-v1.json`
- `docs/STRATA-001-PILOT-v1.md`

## Design

- 6 blocks
- 2 MemoryHigh levels: 160 / 168 MiB
- 3 arms
- 36 trials
- HOT anon 64 MiB
- COLD file 96 MiB
- reusable pread buffer 4 MiB
- MemoryMax 320 MiB

## Primary pilot estimand

Paired runner-block HOT-residency difference:

`DIRECT_PREAD - BUFFERED_PREAD`

No hypothesis gate.

## Next action

Implement workload, schedule/aggregator tests, and a bounded pilot workflow.

## Authority boundary

Pilot only.
