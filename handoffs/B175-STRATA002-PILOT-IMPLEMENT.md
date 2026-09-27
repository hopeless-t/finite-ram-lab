# Bounce Handoff

> **Bounce ID:** B175
> **Status:** COMPLETE / STRATA-002-PILOT-v1 IMPLEMENTED

## Added

- `src/finite_ram_lab/strata002_pilot_workload.py`
- `src/finite_ram_lab/strata002_pilot_study.py`
- `tests/test_strata002_pilot.py`
- `.github/workflows/strata-002-pilot.yml`

## Arms

- buffered
- buffered + NOREUSE
- buffered + sliding DONTNEED
- direct reference

## Controls

- Linux >=6.3 semantics required for NOREUSE arm;
- advice result recorded explicitly;
- pre-scan file coldness enforced;
- no O_DIRECT fallback;
- scan pressure deltas captured;
- HOT anonymous residency retained as guardrail;
- manual-only workflow;
- no hypothesis gate.

## Next action

Read ordinary CI for B175 exactly once.

- SUCCESS → launch one bounded STRATA-002 pilot next turn/next bounce.
- pending → checkpoint EXTERNAL_WAIT.
- failure → inspect failure only.

## Authority boundary

Research only.
