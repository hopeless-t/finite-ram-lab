# FR-FP-004 — Predictive residency phase diagram

Status: **SYNTHETIC PHASE MAP CANDIDATE**

Parent: **FR-FP-003**

## Question

FR-FP-003 showed that a predictive cold-tier policy can avoid semantic OOM
while using less I/O than always-preemptive transfer.

That result depends on slack.

FR-FP-004 maps the boundary over:

- transfer lead time;
- hot-state budget;
- predictor margin.

The goal is to separate policy quality from physical deadline feasibility.

## Sweep

Frozen grid:

- transfer lead: 1, 2, 3, 4 steps;
- hot budget: 4, 6, 8, 10 states;
- prediction margin: -1, 0, 1, 2, 3, 4;
- 1,000 deterministic Monte Carlo trajectories from FR-FP-002.

For each lead/budget cell:

1. evaluate ALWAYS_PREEMPTIVE;
2. evaluate every predictive margin;
3. keep zero-OOM predictive candidates only;
4. select the candidate with minimum cold writes;
5. compare its I/O against always-preemptive.

## Phases

DEADLINE_INFEASIBLE
: even always-preemptive transfer misses the hot-budget deadline.

PREDICTION_HAS_NO_MATERIAL_IO_ADVANTAGE
: zero-OOM prediction exists, but saves at most 5 percent cold writes.

PREDICTION_SAVES_IO
: zero-OOM prediction saves more than 5 percent cold writes.

NO_ZERO_OOM_PREDICTIVE_CANDIDATE
: reserved for a case where always-preemptive is feasible but the tested
  predictor-margin family is insufficient.

## Expected geometry

The phase map should show:

- more hot-budget slack increases predictive I/O savings;
- longer transfer lead reduces the room for selective transfer;
- sufficiently long lead plus very tight budget creates a deadline-infeasible
  region.

The important result is the third point.

If even always-preemptive transfer cannot meet the deadline, no better decision
policy can fix the current transfer surface.

The system must instead change one of:

- budget;
- transfer latency;
- retained-state size;
- tier bandwidth;
- application convergence/reclaimability timing.

## Why Monte Carlo belongs here

This is not an exact workflow-topology question.

The phase classification is an aggregate over heterogeneous synthetic
trajectories and an uncertain prediction policy family.

Monte Carlo is therefore part of the evidence rather than ritual overhead.

## North-Star consequence

The Governor state is no longer only:

    current pressure

It needs at least:

    hot-budget slack
    transfer lead time
    predicted time-to-reclaimability

and must recognize:

    feasible optimization region
    versus
    physically deadline-infeasible region

That distinction prevents endless policy search when the resource geometry
itself cannot satisfy the task.

## Claim ceiling

**SYNTHETIC_PREDICTIVE_RESIDENCY_PHASE_BOUNDARY_ONLY**
