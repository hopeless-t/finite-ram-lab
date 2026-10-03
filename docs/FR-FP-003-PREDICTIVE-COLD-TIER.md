# FR-FP-003 — Predictive cold-tier transfer

Status: **SYNTHETIC EXPERIMENT CANDIDATE**

Parent: **FR-FP-002**

## Why

FR-FP-002 showed a new fail-closed state:

    endpoint is not yet safe to substitute
    + hot budget is exhausted
    = semantic OOM

The cold-tier arm avoided that state because transfer was modeled as
instantaneous.

Real transfers are not instantaneous.

FR-FP-003 adds a frozen two-step transfer lead time and asks whether the
Governor must act before pressure is already present.

## Policies

REACTIVE_TRANSFER
: starts a cold transfer only when hot occupancy reaches the budget.

ALWAYS_PREEMPTIVE
: starts transfers whenever old hot history exists.

PREDICTIVE_TRANSFER
: estimates time-to-safe-endpoint from only the currently observed gap/residual
  trend and starts transfer when predicted reclaimability will arrive too late
  relative to budget slack and transfer latency.

## No future leakage

The predictor uses only:

- current gap;
- previous gap;
- previous-previous gap;
- current residual.

A frozen test mutates all future trajectory values and requires the prediction
at the current step to remain identical.

## Frozen intuition

With transfer lead time L:

    current pressure
    !=
    enough time to react

The relevant comparison becomes:

    time to hot-budget exhaustion
    versus
    transfer lead time
    versus
    estimated time to semantic reclaimability

## Results expected by the contract

At budget 8:

- reactive transfer retains a high semantic-OOM rate;
- predictive transfer drives the frozen OOM rate to zero;
- predictive transfer uses materially fewer cold writes than always-preemptive.

At budget 4:

- prediction still avoids OOM;
- its I/O advantage shrinks because there is very little slack.

This is the expected pressure knee: when the budget is extremely tight, the
Governor has less room to be selective.

## Why this matters

The first Finite RAM Governor was reactive to current state.

This experiment introduces an explicit future variable:

    ETA_reclaimable

That moves the Governor toward:

    observe latent trajectory
      -> estimate reclaimability arrival
      -> compare with pressure horizon
      -> move state before the deadline

which is the predictive form of semantic residency control.

## Claim ceiling

**SYNTHETIC_PREDICTIVE_TRANSFER_TIMING_ONLY**
