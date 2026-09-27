# Bounce Handoff

> **Bounce ID:** B173
> **Status:** COMPLETE / STRATA-002 COUNCIL CONVERGED

## Decision

Open STRATA-002 — Advisory Cold-Stream Cache Control.

Compare:

- ordinary buffered preadv;
- buffered + POSIX_FADV_NOREUSE;
- buffered + sliding POSIX_FADV_DONTNEED;
- O_DIRECT reference.

## Pilot

- MemoryHigh 160 MiB only;
- MemoryMax 320 MiB;
- HOT anon 64 MiB guardrail;
- COLD file 96 MiB;
- buffer 4 MiB;
- 8 blocks;
- 32 trials.

## Primary outcomes

- MemoryHigh event delta;
- memory.current;
- memory.peak;
- post-scan file residency.

## Scientific consequence

Do not force a confirmatory HOT-residency study where STRATA-001 observed zero headroom.

Move toward a practical application-level COLD-stream signal.

## Next action

Freeze STRATA-002-PILOT-v1 contract.

## Authority boundary

Research only.
