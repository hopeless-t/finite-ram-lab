# MATH-002 pmndrs/math Geometric Lens v1

> **Status:** FROZEN SECONDARY DESIGN / NOT A PRIMARY DECISION RULE
> **Dependency:** `pmndrs/math@98762395c1f34d7d594d31165e8005fd6915c431`
> **Authority:** HOSTED_RESEARCH_ONLY

## Purpose

Use `pmndrs/math` as an independent structural lens over MEMCG-003 output.

This does **not** replace the preregistered threshold / MDL / Bayesian K analysis.

The goal is to ask whether the experimental response occupies a geometric region that is visibly distinct from controls, and whether the apparent transition near K=7 is an extreme/boundary feature rather than only a scalar threshold artifact.

## Why pmndrs/math is useful here

Relevant APIs confirmed in the pinned source:

- `quickhull2(points)`
- `quickhull3(points)`
- vector helpers
- seeded RNG: `mulberry32`, `isaac32`, `isaac64`
- `binomial`
- shape primitives / polygon helpers

The library is data-oriented and allocation-light, which makes it suitable for deterministic sidecar analysis.

## Input

Canonical MEMCG-003 aggregate only.

If duplicate workflow runs exist, the canonical run is selected **before** reading scientific results.

For the current launch:
- canonical run: `36459951576`
- duplicate/noncanonical run: `36459972685`

The duplicate must not be used for model selection.

## Point-cloud constructions

### Response plane

For every probe record define:

`P2 = (stock_drop_pages, probe_delta_pages)`

Label by:
- arm
- block
- challenger count m

Compute 2D convex hulls separately for:
- DISTINCT_CHURN
- pooled controls

Report:
- hull vertices
- hull area
- whether large-response points are hull-extreme
- distance of each distinct-churn point from the control hull when polygon helpers permit

### Threshold-response plane

Define:

`T2 = (m, max(stock_drop_pages, probe_delta_pages))`

Compute hull per block and pooled.

Question:
does the transition near m=7 form a stable outer-hull kink/extreme across blocks?

### Three-dimensional envelope

Define:

`P3 = (m, stock_drop_pages, probe_delta_pages)`

Use `quickhull3` only as a secondary envelope diagnostic.

Do not convert hull membership into a causal verdict.

## Seeded permutation null

Use `mulberry32` with fixed seed:

`20260929`

Within each block:
- preserve response vectors;
- permute challenger-count labels among DISTINCT_CHURN records;
- recompute a preregistered geometric transition score.

Primary geometric score:

`G = count of blocks whose maximum response-hull extremum occurs at m in {6,7,8}`

Run 100,000 permutations.

Report:
- observed G
- null histogram
- empirical tail probability with +1 correction

This is a structural permutation diagnostic, not a standalone causal p-value.

## Guardrails

- Primary MEMCG-003 decision remains threshold/Bayesian/LOBO.
- Geometry cannot rescue a failed primary experiment.
- Geometry may generate the next hypothesis.
- Duplicate workflow output cannot be pooled with canonical output.
- No visual impression may override machine-readable metrics.

## Expected value

If K=7 is real and clean:
- distinct-churn response cloud should extend beyond controls;
- strongest geometric extremum should cluster near m=7;
- seeded permutation should rarely reproduce the same alignment.

If primary K=7 fails but geometry shows another stable boundary:
- treat that as a new hypothesis, not a reinterpretation of the preregistered result.

## Launch boundary

Wait for canonical MEMCG-003 result.
No separate hosted launch yet.
No local-PC execution.
