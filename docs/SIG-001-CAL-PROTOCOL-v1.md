# SIG-001-CAL-PROTOCOL-v1

> **Status:** FROZEN PROTOCOL / OFFLINE ONLY

## Purpose

Calibrate a future-informed semantic ACT/NO-ACT provider against the empirical action-cost contract derived from EXP-003.

The protocol produces evidence only. It cannot execute a memory action.

## Frozen files

- `specs/SIG-001-CAL-PROTOCOL-v1.json`
- `schemas/SIG-001-CAL-MANIFEST.schema.json`
- `schemas/SIG-001-CAL-PREDICTION.schema.json`
- `schemas/SIG-001-CAL-OUTCOME.schema.json`

## Calibration epoch binding

A calibration epoch binds all of:

- provider ID;
- provider version;
- decision-rule ID;
- epoch ID;
- environment digest;
- prediction-horizon ID.

Changing any field creates a new evidence epoch. Evidence must not be silently pooled across epochs.

## Prediction seal

Predictions live in a separate JSONL artifact.

Before outcomes are attached:

1. compute SHA-256 of the exact prediction artifact;
2. place the digest in the manifest;
3. record an external seal reference such as a Git commit or another immutable/timestamped evidence reference.

The offline tool verifies the digest. It records the external seal reference but does not claim to independently prove wall-clock time.

## Independent evidence unit

Version 1 permits at most one event per `independence_unit_id`.

This is deliberately strict.

The SIG-001 design-MC sample sizes are counts of independent calibration units, not raw correlated windows.

If independence cannot be defended, v1 returns NOT_CERTIFIED and a cluster-robust extension must be researched separately.

## Labels and decisions

Prediction:

- ACT
- NO_ACT
- ABSTAIN

Ground truth:

- misaligned
- aligned

For safety accounting:

`ABSTAIN -> NO_ACT`

Therefore:

- q = misaligned / all independent units;
- sensitivity = ACT among misaligned;
- specificity = NO_ACT or ABSTAIN among aligned.

## Fixed decision rule

Provider thresholds and decision logic must be fixed before the epoch begins.

The optional prediction score is audit-only in v1.

No threshold may be selected or tuned using the same epoch and then treated as if it had been fixed in advance.

## Statistical contract

Use the same SIG-001 design contract:

- family-wise alpha = 0.05;
- Bonferroni over q, sensitivity, specificity and empirical action-cost ratio;
- exact one-sided Clopper-Pearson lower bounds for q, sensitivity and specificity;
- fail-closed lower bootstrap quantile of b/h from the frozen EXP-003 input;
- log/geometric total-work is primary;
- arithmetic total-work is secondary only.

Primary certification condition:

`specificity_L > 1 - q_L * sensitivity_L * ratio_L / (1 - q_L)`

If any required quantity is invalid, missing or structurally unverifiable, output NOT_CERTIFIED.

## Output authority

Only two statuses exist:

- CERTIFIED
- NOT_CERTIFIED

CERTIFIED means the observational evidence clears the frozen statistical admission rule.

It still does **not** execute ACT.

NOT_CERTIFIED maps to NO-ACT at any future authority boundary.

## Fail-closed validation

The offline tool must reject:

- duplicate event IDs;
- duplicate independence-unit IDs;
- prediction/outcome event-set mismatch;
- outcome timestamp not later than prediction timestamp;
- prediction-file digest mismatch;
- schema mismatch;
- empty external seal reference;
- mixed epoch/provider/rule/environment semantics;
- no misaligned or no aligned evidence sufficient for finite bounds.

## Non-authority

This protocol does not select a provider, establish production exchangeability, execute PAGEOUT or authorize deployment.
