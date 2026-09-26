# Bounce Handoff

> **Bounce ID:** B139
> **Status:** COMPLETE / SIG-001 OBSERVATIONAL PROTOCOL COUNCIL CONVERGED

## Trigger

B138 quantified the calibration burden, but the design Monte Carlo assumes independent Bernoulli calibration units.

Before measuring a real provider, the evidence unit and provenance rules must be frozen.

## Fresh repo check

No existing calibration manifest, provider-version contract, prediction seal, or independence-unit schema exists in finite-ram-lab.

## Council convergence

### Statistics

The N values from SIG-001 Design-MC must be interpreted as **independent calibration units**, not arbitrary correlated time windows.

Version 1 must therefore fail closed if multiple observations share the same independence-unit identifier.

The existing exact one-sided Clopper-Pearson rule remains valid only for the frozen independent-unit model.

### Leakage control

The provider decision rule must be frozen before a calibration epoch begins.

Changing any of the following starts a new epoch and invalidates pooling with prior evidence:

- provider implementation/version;
- decision threshold/rule;
- prediction horizon semantics;
- environment contract.

Threshold tuning on the same observations later used for certification is prohibited in v1.

### Prediction-before-outcome provenance

Predictions must be written before realized alignment is known.

Version 1 uses separate prediction and outcome files plus a prediction manifest containing:

- prediction-file SHA-256;
- provider/version/rule identifiers;
- epoch identifier;
- environment digest;
- prediction-horizon identifier;
- external seal reference.

The tool can verify the digest and structure.
The external seal reference records the mechanism that timestamped/committed the prediction artifact; the tool does not claim to independently prove wall-clock time.

### Decision semantics

Provider output:

- ACT;
- NO_ACT;
- ABSTAIN.

For safety accounting, ABSTAIN maps to NO_ACT.

Ground truth:

- misaligned;
- aligned.

Calibration quantities remain:

- q = P(misaligned);
- t = P(ACT | misaligned);
- s = P(NO_ACT or ABSTAIN | aligned).

### Fail-closed admission

Use the same B125/B132 family-wise confidence contract.

Output only:

- CERTIFIED; or
- NOT_CERTIFIED.

NOT_CERTIFIED always means NO-ACT at the authority boundary.

Arithmetic evidence cannot override a failure on the primary log/geometric surface.

### Correlation boundary

If independence cannot be defended, v1 must refuse certification rather than silently count correlated windows as independent evidence.

A cluster-robust extension is a separate future research item.

## Decision

Freeze **SIG-001-CAL-PROTOCOL-v1** and implement an offline-only validator/calibrator.

It must not execute PAGEOUT or call any memory-action API.

## Next action

Freeze the manifest/prediction/outcome schemas and calibration contract.

## Authority boundary

Observation and certification analysis only.
No provider is selected.
No memory intervention is authorized.
