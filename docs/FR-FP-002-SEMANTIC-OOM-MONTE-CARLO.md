# FR-FP-002 — Semantic OOM Monte Carlo

Status: **SYNTHETIC EXPERIMENT CANDIDATE**

Parent: **FR-FP-001**

## Question

FR-FP-001 defined convergence-conditioned trajectory reclaimability.

FR-FP-002 asks a smaller executable question:

> Under finite hot-state capacity, what happens when memory is physically
> reclaimable but the application does not yet have semantic permission to
> discard the trajectory?

This is a synthetic model, not an OS or model-memory result.

## Semantic OOM proxy

A semantic OOM event occurs when:

1. hot state exceeds the frozen budget;
2. the current policy has no semantics-preserving hot reclaim action available.

This differs from a generic physical OOM.

A policy may have plenty of bytes it could technically free, while freeing them
would violate its declared semantic contract.

## Trajectory families

The 1,000-episode deterministic Monte Carlo includes:

- contraction;
- slow drift;
- false-small-residual then jump;
- oscillatory convergence.

The negative controls are intentional.

Slow drift and false-small-residual trajectories create cases where a small
local update does not imply endpoint sufficiency.

## Policies

FULL_TRAJECTORY
: never discards history.

PREMATURE_TERMINAL
: switches to endpoint-only immediately.

AGE_ONLY
: keeps only the newest two states regardless of semantics.

RESIDUAL_ONLY
: switches to endpoint-only when local residual crosses the threshold.

VALIDATED_ENDPOINT
: requires both residual and endpoint-gap thresholds.

COLD_TIER_VALIDATED
: preserves not-yet-reclaimable history in a cold tier under pressure, then
  discards it only after endpoint validation.

## Pressure sweep

Hot-state budgets:

    2, 4, 8, 16

Metrics:

- semantic survival;
- semantic OOM;
- semantic corruption;
- peak hot states;
- cold writes;
- reclaim step;
- corruption by trajectory family.

## Frozen hypotheses

### H1 — residual alone is unsafe

At effectively unpressured budget 16, RESIDUAL_ONLY must show a material
semantic-corruption rate.

This isolates the false-small-residual problem from memory pressure.

### H2 — endpoint validation is fail-closed

VALIDATED_ENDPOINT must show zero semantic corruption in the frozen fixture.

Under tighter budgets it is allowed to report semantic OOM instead of silently
discarding live state.

### H3 — cold tier trades I/O for semantic survival

COLD_TIER_VALIDATED must avoid both corruption and semantic OOM in the frozen
tight-budget fixture, while paying positive cold-write cost.

This is not a claim that SSD is always optimal.

It demonstrates the shape of the trade:

    preserve semantics
      -> consume slower-tier capacity / I/O
      -> delay irreversible discard

## Pseudo-Council

Methodologist
: requires residual-only negative control to fail safely as a hypothesis.

Systems
: requires hot and cold costs to remain separate.

Falsifier
: requires slow-drift, false-small-residual, and oscillatory families.

Evidence reviewer
: keeps the claim ceiling synthetic.

## Why this matters for the North Star

The experiment distinguishes three failure modes that a plain RSS threshold
cannot:

1. memory-heavy but semantically safe retention;
2. memory-light but semantically corrupt premature discard;
3. fail-closed semantic OOM because no safe hot reclaim exists yet.

That gives the future Governor a better target than physical pressure alone.

A predictive Governor can eventually ask:

    when will semantic reclaimability arrive?
    can cold tier bridge the interval?
    what resident budget is required until then?

## Next empirical step

The next upgrade should replace this synthetic trajectory with a bounded real or
upstream-compatible recurrent workload that exposes:

- convergence residual;
- endpoint-gap metric;
- retained state bytes;
- cold-tier / replay cost;
- correctness.

No local memory-gain claim is made before that transition.

## Claim ceiling

**SYNTHETIC_TRAJECTORY_RECLAIMABILITY_AND_SEMANTIC_OOM_ONLY**
