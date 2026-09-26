# Bounce Handoff

> **Bounce ID:** B141
> **Status:** COMPLETE / SIG-001 OFFLINE CALIBRATOR IMPLEMENTED

## Completed

- `src/finite_ram_lab/sig001_calibration.py`
- `tests/test_sig001_calibration.py`

## Implementation properties

- exact frozen protocol equality is required;
- prediction JSONL SHA-256 is verified against the manifest;
- manifest/provider/version/rule/epoch/environment/horizon binding is validated;
- event IDs and independence-unit IDs must be unique;
- prediction/outcome event sets must match exactly;
- outcome timestamp must be later than prediction timestamp;
- ABSTAIN maps to NO_ACT for specificity;
- q/sensitivity/specificity use exact one-sided Clopper-Pearson lower bounds;
- primary log/geometric and secondary arithmetic action-cost ratios reuse the frozen EXP-003 bootstrap contract;
- only CERTIFIED / NOT_CERTIFIED decisions are produced after successful validation;
- CLI structural failures write NOT_CERTIFIED and exit non-zero.

## Tests

Coverage includes:

- strong provider certification;
- unsafe provider fail-closed result;
- prediction digest mismatch;
- duplicate independence unit;
- hindsight timestamp violation;
- modified statistical protocol rejection.

## Explicit non-authority

The module imports no memory-action workload and exposes no PAGEOUT operation.

## Next action

Read ordinary CI for B141 exactly once in a fresh bounce.

## Authority boundary

Offline certification implementation only.
No provider or memory intervention is authorized.
