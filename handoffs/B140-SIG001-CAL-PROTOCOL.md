# Bounce Handoff

> **Bounce ID:** B140
> **Status:** COMPLETE / SIG-001 CALIBRATION PROTOCOL FROZEN

## Frozen artifacts

- `specs/SIG-001-CAL-PROTOCOL-v1.json`
- `schemas/SIG-001-CAL-MANIFEST.schema.json`
- `schemas/SIG-001-CAL-PREDICTION.schema.json`
- `schemas/SIG-001-CAL-OUTCOME.schema.json`
- `docs/SIG-001-CAL-PROTOCOL-v1.md`

## Key decisions

- N means independent calibration units;
- one event per independence unit in v1;
- provider/version/rule/epoch/environment/horizon are bound;
- prediction artifact must be digest-sealed before outcomes;
- ABSTAIN maps to NO_ACT;
- score is audit-only and cannot be tuned post hoc;
- only CERTIFIED / NOT_CERTIFIED outputs exist;
- the tool is offline-only and has no memory-action authority.

## Next action

Implement the offline validator/calibrator and unit tests only.

## Authority boundary

Protocol freeze only.
No real provider is calibrated and no memory intervention is authorized.
