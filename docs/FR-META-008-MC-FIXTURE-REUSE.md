# FR-META-008 — KSLA Monte Carlo Fixture Reuse

Status: **DETACHED PROVISIONAL UNTIL FR-META-007 RECEIPT**

Parent: **FR-META-007**

## Hotspot biopsy

The bounded-idiocy test class calls the same deterministic 200,000-episode
matched Monte Carlo panel in three separate tests.

The three assertions inspect different fields of one immutable result, so
recomputing the entire panel has no additional evidentiary value.

## Optimization

Compute run_panel once in setUpClass and share the result across the class.

Nothing in the scientific panel changes:

- MC episodes remain 200,000;
- matched random tape remains identical;
- analytic comparison remains identical;
- utility thresholds remain identical;
- claim ceiling remains identical.

Structural test-harness work:

- baseline: 3 x 200,000 = 600,000 episode evaluations;
- candidate: 1 x 200,000 = 200,000;
- reduction: 66.67%.

## Why no extra Monte Carlo is used

The optimization removes exact duplicate calls to the same deterministic panel.
Another Monte Carlo study would only repeat the redundancy being removed.

## Speculative publication rule

This candidate is built as a detached child while FR-META-007 is in
qualification.

It may receive a branch ref only after the FR-META-007 qualification receipt is
frozen.

## Claim ceiling

**TEST_FIXTURE_REUSE_OPTIMIZATION_ONLY**
