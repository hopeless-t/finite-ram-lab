# Bounce Handoff

> **Bounce ID:** B178
> **Status:** COMPLETE / STRATA-002-PILOT-v1 LAUNCHED

## Launch mechanism

The pilot workflow now also triggers on push to main only when this file changes:

`.github/workflows/strata-002-pilot.yml`

The scientific contract is unchanged.

## Pilot

- 8 independent blocks
- 32 total trials
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- HOT anon 64 MiB guardrail
- COLD file 96 MiB
- arms:
  - buffered
  - buffered_noreuse
  - buffered_dontneed
  - direct

## Expected external effect

Exactly one bounded STRATA-002-PILOT-v1 run should be created from this commit.

## Next action

Discover the pilot run for this launch commit exactly once.

## Authority boundary

Research only.
