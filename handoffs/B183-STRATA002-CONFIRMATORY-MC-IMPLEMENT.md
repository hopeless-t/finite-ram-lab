# Bounce Handoff

> **Bounce ID:** B183
> **Status:** COMPLETE / STRATA-002 CONFIRMATORY MC IMPLEMENTED

## Added

- `src/finite_ram_lab/strata002_confirmatory_mc.py`
- `tests/test_strata002_confirmatory_mc.py`
- `.github/workflows/strata-002-confirmatory-mc.yml`

## Properties

- deterministic seed;
- 200k replicates per frozen candidate;
- chunked simulation;
- exact efficacy sign gate;
- conservative CP lower-bound verification;
- Student-t one-sided latency guardrail;
- joint design assurance;
- no physical experiment launch.

## Next action

Read ordinary CI for B183 exactly once.

- SUCCESS → launch one design-MC workflow.
- pending → checkpoint EXTERNAL_WAIT.
- failure → inspect failure only.

## Authority boundary

Design only.
