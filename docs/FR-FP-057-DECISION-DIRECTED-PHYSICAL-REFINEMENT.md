# FR-FP-057 — Decision-directed physical refinement

Status: **HOSTED PHYSICAL POLICY-REFINEMENT CANDIDATE**

Parent: **FR-FP-056**

## Why

FR-FP-056 exposes four hosted physical policy anchors and explicitly warns that
untested intermediate policies may be better.

The wrong response is to run every rent point physically.

The twelve FP054 rent points collapse to only eight unique five-phase placement
paths.

Four unique paths are already physically qualified.

Exactly four remain.

## Deduplicate before measurement

The shadow rent sweep contains equivalent rent values that select the same full
placement path.

Examples:

    0 / 0.025 / 0.05
      -> one identical path

    0.10 / 0.125
      -> one identical path

    0.15 / 0.175
      -> one identical path

Physical evidence is acquired per unique policy path, not per arbitrary scalar
rent value.

## New physical representatives

Measure only:

    0.075
    0.15
    0.20
    0.30

These four representatives cover every unique path missing from the FP055
physical evidence.

Each arm uses the qualified size-aware physical actuator and verifies actual
page-cache residency against the shadow path.

## Full physical lower envelope

After the four measurements:

- all eight unique FP054 policy paths have hosted physical evidence;
- the typed resident/service/actuation Pareto frontier is recomputed;
- when an external memory rent is explicitly supplied, the exact lower envelope
  among the eight physically measured policy lines is compiled into intervals.

No fake scalar gain is exported.

## Meta consequence

Experiment planning itself follows Finite RAM:

> normalize equivalent hypotheses first, then acquire physical evidence only
> once per decision-distinct state.

## Claim ceiling

**EIGHT_UNIQUE_HOSTED_PHYSICAL_POLICY_PATHS_FROM_THE_FP054_TWELVE_POINT_RENT_SWEEP_ONLY**
