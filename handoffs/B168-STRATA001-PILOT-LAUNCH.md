# Bounce Handoff

> **Bounce ID:** B168
> **Status:** COMPLETE / STRATA-001-PILOT-v1 LAUNCHED

## Launch mechanism

The pilot workflow now also triggers on a push to main only when this file changes:

`.github/workflows/strata-001-pilot.yml`

This is a launch transport workaround for the connected GitHub surface, which does not expose workflow_dispatch mutation.

## Scientific contract

Unchanged:

- 6 runner blocks;
- 36 total trials;
- MemoryHigh 160 / 168 MiB;
- MemoryMax 320 MiB;
- HOT anonymous 64 MiB;
- COLD file 96 MiB;
- arms MMAP / BUFFERED_PREAD / DIRECT_PREAD;
- pilot-only inference boundary.

## Expected external effect

Exactly one bounded STRATA-001-PILOT-v1 run should be created from this commit.

## Next action

Discover the pilot run for this launch commit exactly once.

- completed SUCCESS → inspect aggregate artifact;
- queued/in_progress → checkpoint EXTERNAL_WAIT;
- failure → inspect only the failing job.

## Authority boundary

Pilot only.
