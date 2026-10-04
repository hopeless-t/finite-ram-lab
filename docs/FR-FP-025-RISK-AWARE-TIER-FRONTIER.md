# FR-FP-025 — Risk-aware WARM/COLD tier frontier

Status: **REUSED EVIDENCE DECISION-FRONTIER CANDIDATE**

Parent: **FR-FP-024**

## Why

FR-FP-015 expressed WARM/COLD break-even using one measured restore penalty.

FR-FP-024 now gives a better restore state:

- a robust current-run COLD baseline;
- a residual tail prior;
- an empirical WARM restore distribution.

The tier decision can therefore become probabilistic without inventing one
hidden universal utility.

## State

For an 8 MiB state:

    b = current-run COLD baseline
    R = residual multiplier
    W = WARM restore latency
    p = probability the state is reused

External policy supplies:

    lambda = value/cost of retaining 1 MiB WARM, measured in latency-equivalent
             ms per MiB
    D      = restore deadline
    epsilon = tolerated per-state deadline-miss probability

## Expected break-even surface

If the state is reused, the additional restore penalty from COLD rather than
WARM is:

    (bR - W)+

where x+ = max(x, 0).

Expected penalty per retained state:

    p E[(bR - W)+]

COLD releases approximately 8 MiB of WARM page-cache residency in this frozen
fixture.

Therefore the break-even shadow price is:

    lambda_star
      =
    p E[(bR - W)+] / 8 MiB

If the external memory shadow price exceeds lambda_star, the expected memory
benefit is large enough to pay the empirical promotion penalty.

## Deadline surface

Expected cost is not enough.

The unconditional per-state deadline-miss probability is:

    q_D
      =
    p P(bR > D)

COLD is deadline-eligible only if:

    q_D <= epsilon

## Routing

COLD is eligible only when both independent conditions are satisfied:

    lambda >= lambda_star
    q_D <= epsilon

Otherwise keep the state WARM or choose another tier/policy.

The research code exposes the surface.

It does not pick lambda or epsilon for the user/application.

## Why two constraints stay separate

A low expected penalty can still contain an unacceptable deadline tail.

A strict deadline can forbid COLD even when COLD is attractive in average
memory/latency tradeoff.

Collapsing both into one undocumented scalar utility would hide that distinction.

## Evidence

No new physical run is scheduled.

The residual and WARM priors are built from the existing fifteen hosted runs.

The v0.1 grid sweeps:

- current baselines: 3 / 5 / 10 / 25 / 100 ms;
- reuse probabilities: 0.10 / 0.25 / 0.50 / 0.75 / 1.00;
- deadlines: 10 / 25 / 50 / 100 ms;
- miss tolerances: 1% / 5% / 10% / 25%.

## North-Star consequence

The Governor no longer needs one hardcoded tier threshold.

It can carry:

- tiny calibrated current state;
- compact empirical tail priors;

and accept application-specific policy constraints at decision time.

## Claim ceiling

**EMPIRICAL_FRONTIER_FROM_REUSED_8MIB_HOSTED_RESTORE_EVIDENCE_ONLY**
