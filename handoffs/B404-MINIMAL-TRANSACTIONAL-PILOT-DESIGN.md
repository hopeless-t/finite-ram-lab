# B404 — Minimal transactional spawn pilot design

## Status

COMPLETE / DESIGN FROZEN / NO PHYSICAL RUN.

## Objective

Choose the smallest information-maximizing physical pilot for the new B400/B403 transactional path before any reliability certification.

## Frozen design

Spec:

- specs/TRANSACTIONAL-SPAWN-PILOT-v1.json

Math/design:

- docs/MATH-020-TRANSACTIONAL-SPAWN-PILOT-DESIGN.md

### Normal lane

12 scientific identities:

- b62: 4
- b63: 4
- b64: 4

No replacement identities.

### Sentinel lane

One non-scientific forced unexpected-refill sentinel.

Purpose:

- prove invalidation cannot commit;
- prove stale epoch receipts cannot authorize a new epoch;
- prove fresh direct Q64 is required after re-prime.

### Re-prime

- max_reprimes = 2
- mode = HARD_NEW_WORKER_CGROUP
- at most 3 epochs per admitted identity

Hard re-prime is chosen first for interpretability, receipt isolation, and safe-span reset.

Soft same-worker re-prime remains a later optimization question.

## Why this is not certification

Even 12/12 accepted correct outcomes would provide only an approximately 77.9% one-sided 95% all-success correctness floor.

Four per arm would provide only about 47.3%.

Therefore the panel is explicitly architecture smoke, not reliability evidence.

## OBS-006 sensitivity only

Using Jeffreys posterior from 14/16 state preservation:

p_preserve ~ Beta(14.5,2.5)

the posterior-predictive chance of at least one invalidation in 12 exchangeable future attempts is about 76.6%.

This is not a transfer claim.

The sentinel exists so invalidation/re-prime coverage does not depend on natural state loss.

## Stop rules

Immediate scientific stop:

- any TARGET_FAIL from a complete uninterrupted verified normal-lane epoch.

Instrumentation hold:

- trace gap;
- CPU mismatch;
- worker error.

State invalidation:

- unexpected refill;
- drain;
- PTE growth.

These may hard re-prime while budget remains.

Budget exhaustion:

ABORTED / NO_RESULT.

No automatic scale expansion.

## Launch boundary

Physical execution remains unauthorized.

Before launch:

1. native per-touch trace markers;
2. direct charge64/refill63/drain observer wiring;
3. positive release-only classifier;
4. per-epoch packet archive;
5. synthetic sentinel replay;
6. CI;
7. Human authorization for any paid/gated compute.

## Next

Implement the native trace/observer wiring without launching the pilot.
