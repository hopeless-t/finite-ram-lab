# B405 — Chapter II transaction perturbation matrix

## Status

DESIGN FROZEN / NO PHYSICAL RUN.

## Main hypothesis

Once a Q64 reset is directly verified, the stock arithmetic remains deterministic until a discrete observer-visible invalidating event occurs.

State-preserving contamination and state-destroying transitions must be tested causally rather than inferred from passive outcomes.

## Frozen matrix

- CLEAN x4
- RELEASE_ONLY x4
- UNEXPECTED_REFILL x4
- PTE_GROWTH x4

Total scientific mechanism-challenge identities: 16.

No reliability claim.

## Predictions

RELEASE_ONLY:

- record the release;
- preserve expected residual;
- preserve canonical b63 terminal phase.

UNEXPECTED_REFILL:

- INVALIDATE;
- no TARGET_FAIL;
- no COMMIT in the invalidated epoch;
- fresh direct Q64 required after re-prime.

PTE_GROWTH:

- INVALIDATE before COMMIT;
- guard precedence overrides apparent target match.

CLEAN:

- canonical verified transaction path.

## Hazard telemetry

Record per packet:

- touch_index_since_verified;
- elapsed_ns_since_verified;
- expected_residual_before;
- expected_residual_after;
- invalidator type.

This creates the first epoch-hazard atlas without assuming a memoryless per-touch failure model.

## Order

1. B404 native observer/epoch wiring pilot.
2. TX-PERTURBATION-MATRIX-v1.
3. Natural hazard mapping only after the classifier passes causal perturbation.
4. Reliability certification remains deferred.

## Artifacts

- specs/TX-PERTURBATION-MATRIX-v1.json
- docs/MATH-021-CHAPTER-II-TRANSACTION-PERTURBATION-MATRIX.md

## Authority

PAUSE.
No physical run.
No paid runner.
No local-PC execution.
