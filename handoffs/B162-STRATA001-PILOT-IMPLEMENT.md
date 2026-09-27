# Bounce Handoff

> **Bounce ID:** B162
> **Status:** COMPLETE / STRATA-001-PILOT-v1 IMPLEMENTED

## Added

- `src/finite_ram_lab/strata001_pilot_workload.py`
- `src/finite_ram_lab/strata001_pilot_study.py`
- `tests/test_strata001_pilot.py`
- `.github/workflows/strata-001-pilot.yml`

## Implementation controls

- same 4 MiB resident scratch footprint in all three arms;
- DIRECT and BUFFERED both use preadv over the same sized buffer;
- no direct-I/O fallback;
- file coldness checked before each scan;
- HOT anonymous residency observed before retouch;
- cgroup anon/file/swap captured pre-retouch;
- content integrity checked;
- per-block randomized full factorial;
- pilot output contains paired block effects only;
- no hypothesis decision.

## Workflow

Manual-only.

Committing the implementation does not launch the pilot.

## Next action

Read ordinary CI for B162 exactly once.

- SUCCESS → launch one bounded pilot using a self-file-only trigger.
- FAIL → inspect failure only.

## Authority boundary

Pilot only.
