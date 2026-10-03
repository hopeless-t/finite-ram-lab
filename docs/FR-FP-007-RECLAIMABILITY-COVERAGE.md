# FR-FP-007 — Reclaimability timing versus coverage

Status: **SYNTHETIC DECOMPOSITION CANDIDATE**

Parent: **FR-FP-006**

## Why

FR-FP-006 left one repair lever as a model gap:

    reclaimability timing

A natural assumption would be:

> if safe reclaimability simply arrived early enough, the deadline capability
> gap would disappear.

FR-FP-007 tests that assumption directly.

## Frozen baseline

- transfer lead: 4 steps;
- hot budget: 4 states;
- transfer policy: always-preemptive.

Always-preemptive is used deliberately.

The experiment is not asking whether the predictor is clever enough.

It asks whether the underlying application ever supplies a safe reclaimability
event early enough to matter.

## Intervention

For every trajectory that already has a safe endpoint event, shift that event
earlier by:

    0 .. 10 steps

without changing whether the trajectory ever has a safe event.

This cleanly isolates timing from coverage.

## Result shape

Earlier safe reclaimability sharply reduces semantic OOM.

But it does not remove all OOM.

In the frozen 1,000-trajectory panel:

- 806 trajectories reach a safe endpoint inside the horizon;
- 194 never do;
- safe-reclaimability coverage is 80.6%;
- never-safe fraction is 19.4%.

With a sufficiently large timing shift, semantic OOM falls until it reaches
exactly that 19.4% floor.

Further timing improvement does nothing.

## Two failure domains

### TIMING_GAP

A safe endpoint exists, but it arrives too late relative to:

- hot-budget slack;
- transfer lead;
- state growth.

This can potentially be repaired by earlier convergence or earlier endpoint
validation.

### COVERAGE_GAP

No safe endpoint appears in the observed horizon.

This cannot be repaired by shifting the timing of a nonexistent event.

It requires a different application capability:

- better convergence;
- a representation with sufficient endpoint quality;
- a longer allowed horizon;
- a different task contract;
- or a resource path that can retain the live trajectory indefinitely enough.

## Governor consequence

A predictive Governor needs more than:

    ETA_reclaimable

It also needs an estimate or evidence boundary for:

    P(reclaimable within the task horizon)

or an equivalent coverage signal.

If coverage is unknown, an ETA-only policy can become overconfident.

## North-Star consequence

The earlier semantic-OOM expression now decomposes further:

    semantic OOM
      = timing/deadline failures
      + safe-reclaimability coverage failures

The first is a scheduling problem.

The second is an application capability / contract problem.

They should not share one repair loop.

## Claim ceiling

**SYNTHETIC_RECLAIMABILITY_TIMING_AND_COVERAGE_DECOMPOSITION_ONLY**
