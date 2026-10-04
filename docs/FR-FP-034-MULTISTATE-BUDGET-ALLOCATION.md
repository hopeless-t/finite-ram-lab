# FR-FP-034 — Equal-size multi-state WARM budget allocator

Status: **MULTI-STATE SHADOW CANDIDATE**

Parent: **FR-FP-033**

## Why

FR-FP-025 treated memory shadow price lambda as an external policy input.

That is appropriate for a one-state frontier.

A real finite-memory Governor must choose which states remain WARM when multiple
states compete for one finite capacity.

In that setting, lambda should emerge from the budget boundary.

## Frozen shadow fixture

Ten states.

Each state:

    8 MiB

Shared current-run COLD baseline:

    3.299338 ms

from the hosted FR-FP-031 qualification.

Residual COLD multiplier and WARM restore priors:

    reused from the 15 hosted restore runs

No new physical run is scheduled.

## Reuse uncertainty

Each state has 35 reuse observations.

Frozen reuse counts:

    0,1,2,3,4,5,6,7,8,9

Convert each count into a one-sided 95% Clopper-Pearson reuse upper bound.

The allocator therefore uses conservative p_upper rather than a point estimate.

## State value

For state i:

    v_i
      =
    p_upper_i * E[(bR-W)+]

This is the conservative expected restore penalty avoided by keeping the state
WARM.

All states are equal size in this first lane, so value density is:

    v_i / 8 MiB

## Deadline guard

Frozen deadline:

    D = 10 ms

Miss tolerance:

    epsilon = 5%

A state is mandatory WARM when:

    p_upper_i * P(bR>D) > epsilon

This hard constraint is applied before budget optimization.

## Allocation

Sweep WARM capacity from 3 to 10 state slots.

For each feasible budget:

1. place every deadline-mandatory state WARM;
2. fill remaining slots by descending value density;
3. compare against exhaustive search over all equal-size subsets.

Qualification requires exact agreement with exhaustive optimum.

## Endogenous shadow price

At an interior budget boundary:

    max optional COLD value density
      <=
    lambda
      <=
    min optional WARM value density

Thus lambda is no longer an arbitrary external constant.

It becomes the marginal value of one more MiB of WARM capacity.

## North-Star consequence

The control loop advances from:

    one state
      -> given lambda
      -> WARM/COLD

to:

    multiple states
      -> finite shared WARM budget
      -> mandatory correctness/deadline guards
      -> value-ranked residency
      -> endogenous lambda

This is the first direct residency-allocation formulation of the recent
risk-aware Governor line.

## Claim ceiling

**SYNTHETIC_TEN_STATE_EQUAL_SIZE_ALLOCATION_USING_ONE_HOSTED_BASELINE_AND_REUSED_RESTORE_PRIORS_ONLY**
