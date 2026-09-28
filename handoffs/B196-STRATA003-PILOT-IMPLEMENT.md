# Bounce Handoff

> **Bounce ID:** B196
> **Status:** COMPLETE / STRATA-003-PILOT-v1 IMPLEMENTED

## Added

- `src/finite_ram_lab/strata003_pilot_workload.py`
- `src/finite_ram_lab/strata003_pilot_study.py`
- `tests/test_strata003_pilot.py`
- `.github/workflows/strata-003-pilot.yml`

## Key measurement improvement

Each 4 MiB read records:

- pre-advice compact cgroup snapshot;
- post-advice compact cgroup snapshot.

This prevents an end-state-only measurement from hiding transient memory pressure.

## Next action

Read ordinary CI for B196 exactly once.

- SUCCESS → launch one bounded STRATA-003 pilot.
- pending → checkpoint EXTERNAL_WAIT.
- failure → inspect failure only.

## Authority boundary

Hosted research only.
