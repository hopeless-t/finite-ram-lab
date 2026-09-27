# Bounce Handoff

> **Bounce ID:** B180
> **Status:** COMPLETE / STRATA-002 PILOT PASS CANONICALIZED

## Key result

`buffered_dontneed` matched O_DIRECT's pressure footprint in the 32-trial pilot.

Median:

- high events: 0
- memory.current: 75.86 MiB
- post-scan file residency: 0.0

Ordinary buffered:

- high events: 5
- memory.current: 159.32 MiB
- post-scan file residency: 0.8646

NOREUSE did not materially reduce immediate pressure.

## Decision

Advance only `buffered_dontneed` to confirmatory design.

Keep O_DIRECT as a reference mechanism.

Do not advance NOREUSE.

## Next action

Converge confirmatory Council and run Monte Carlo sizing.

## Authority boundary

Hosted research only.
