# Bounce Handoff

> **Bounce ID:** B163
> **Status:** COMPLETE / STRATA-001 PILOT CI QUEUED / TURN CLOSED
> **Turn stop reason:** EXTERNAL_WAIT

## Implementation commit

`4ad80f8f35f18fe6fc35cff699d2fe313ce126bf`

## External run observed exactly once

- run: `36336653793`
- workflow: `CI`
- status: `queued`
- conclusion: not yet available
- attempt: `1`

No repeated polling was performed.

## This turn completed

- B159 — recorded STRATA-001 capability PASS;
- B160 — converged pressure-pilot Council;
- B161 — froze STRATA-001-PILOT-v1;
- B162 — implemented workload, schedule/aggregator, tests, and manual-only workflow;
- B163 — checkpointed queued CI and intentionally closed the turn.

## Frozen pilot

- 6 independent blocks
- MemoryHigh: 160 / 168 MiB
- MemoryMax: 320 MiB
- HOT anonymous: 64 MiB
- COLD file: 96 MiB
- scratch/read buffer: 4 MiB
- arms: MMAP / BUFFERED_PREAD / DIRECT_PREAD
- total trials: 36

## Primary pilot estimand

Paired block difference:

`HOT residency(DIRECT_PREAD) - HOT residency(BUFFERED_PREAD)`

Pilot only; no hypothesis gate.

## Next fresh-turn action

1. rehydrate B163;
2. read CI run `36336653793` exactly once;
3. SUCCESS → launch exactly one bounded STRATA-001-PILOT-v1 run;
4. pending → checkpoint EXTERNAL_WAIT;
5. failure → inspect failing job only.

## Attribution

STRATA-001 remains explicitly inspired by Niko1221/Strata.

No upstream source code is copied.

## Authority boundary

Pilot only.
No confirmatory campaign, deployment, kernel change, or generalized direct-I/O policy is authorized.
