# FR-META-011 — Recursive Research Panel Fixture Reuse

Status: **DOGFOOD PERFORMANCE CANDIDATE**

Parent: **FR-META-010**

## Hotspot

The recursive-research test class invokes the same deterministic run_panel()
twice.

Each invocation includes the L2 robustness campaign with 300 objective-weight
perturbations plus holdout and Goodhart-control evaluation.

The second invocation adds no independent evidence because both tests inspect
different fields of one frozen-seed result.

## Optimization

Compute the panel once in setUpClass and share it across the two assertions.

Nothing in the evaluator changes:

- perturbations remain 300;
- seeds remain unchanged;
- holdout remains unchanged;
- Goodhart control remains unchanged;
- promotion gates remain unchanged.

## Structural reduction

- baseline run_panel calls: 2;
- candidate: 1;
- duplicate panel computation reduction: 50%.

## Claim ceiling

**TEST_FIXTURE_REUSE_OPTIMIZATION_ONLY**
