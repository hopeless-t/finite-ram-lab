# FR-FP-055 — Hosted physical endogenous residency

Status: **HOSTED PHYSICAL RESIDENT-RENT CANDIDATE**

Parent: **FR-FP-054**

## Question

FR-FP-054 showed in exact shadow optimization that a positive resident
byte-time price can make the Governor deliberately leave WARM capacity unused.

FR-FP-055 asks whether that unused capacity is real on hosted Linux.

## Representative policy points

Physically actuate four memory-rent values:

    lambda = 0
    lambda = 0.10
    lambda = 0.25
    lambda = 0.40

All arms use:

- the same ten heterogeneous state sizes;
- the same five online phases;
- the same hard capacity schedule;
- the same size-aware page-cache actuator.

Only the selected WARM sets differ.

## Physical contract

For every phase:

- target WARM files must be >=95% resident;
- target COLD files must be <=10% resident;
- observed resident MiB must match the FR-FP-054 shadow-selected used MiB;
- hard capacity is never exceeded.

The physical resident integral is derived from the five phase snapshots under
the frozen 20-round phase horizon.

## Critical point

The 0.40 arm is allowed to choose:

    zero resident bytes

even when the hard maximum is positive.

This is intentional.

The hard capacity is a safety ceiling, not a utilization target.

## Non-goal

This lane does not claim one lambda is universally optimal.

Memory rent is an explicit policy input.

The result qualifies the physical ability to move along the resident
byte-time frontier.

## Claim ceiling

**HOSTED_PHYSICAL_RESIDENT_RENT_ACTUATION_AT_FOUR_POLICY_POINTS_ON_ONE_VARIABLE_SIZE_FIVE_PHASE_FIXTURE_ONLY**
