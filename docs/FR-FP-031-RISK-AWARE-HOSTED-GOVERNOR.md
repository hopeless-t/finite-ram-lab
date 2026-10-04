# FR-FP-031 — Hosted physical risk-aware Governor

Status: **HOSTED PHYSICAL RISK-AWARE INTEGRATION CANDIDATE**

Parent: **FR-FP-030**

## Why

FR-FP-030 closed the reuse-evidence lifecycle onto real WARM/COLD page-cache
actuation, but used a fixed 10% reuse ceiling.

FR-FP-031 replaces that fixed threshold with the FR-FP-025/026 risk-aware
decision surface.

## Current-run calibration

Before the policy trace:

1. create a separate 8 MiB durable state;
2. keep it physically COLD with POSIX_FADV_DONTNEED;
3. perform two exact restores;
4. use the lower restore latency as the validated TWO_PROBE_MIN baseline.

This is the FR-FP-022/024 robust baseline candidate.

## Risk surface

Reuse the empirical residual multiplier and WARM restore priors.

Frozen external pilot policy:

    memory shadow price lambda = 1.0 ms/MiB
    restore deadline D = 25 ms
    miss tolerance epsilon = 5%

Compute:

    p_cost
      =
    8 MiB * lambda
      /
    E[(bR-W)+]

and:

    p_deadline
      =
    epsilon
      /
    P(bR>D)

Then:

    p_ceiling
      =
    min(1, p_cost, p_deadline)

The current-run physical baseline b therefore changes how much reuse probability
the Governor can tolerate before keeping the state WARM.

## Arms

Physical controls:

- ALWAYS_WARM
- ALWAYS_COLD

Policy comparators:

- FIXED_10PCT_GOVERNOR
- RISK_AWARE_GOVERNOR

Both Governors use the same reuse-evidence lifecycle and k=4 drift alarm.

They differ only in the reuse ceiling.

## Qualification

The risk-aware Governor is not required to use both tiers.

A slow current runner may correctly make COLD ineligible.

Instead the gate requires:

- two physical COLD calibration restores;
- explicit risk-policy inputs;
- a valid dynamic reuse ceiling;
- exact restore integrity;
- physical residency/read costs bounded by ALWAYS_WARM and ALWAYS_COLD;
- the adaptive Governor's COLD exposure moves in the direction implied by the
  dynamic ceiling relative to the fixed 10% comparator.

## North-Star consequence

The closed loop becomes:

    physical current-run calibration
      -> compact residual/WARM priors
      -> explicit memory/deadline policy
      -> reuse ceiling
      -> exact reuse evidence lifecycle
      -> physical WARM/COLD actuation

No universal COLD threshold is required.

## Claim ceiling

**HOSTED_PHYSICAL_RISK_AWARE_TIER_ACTUATION_ON_ONE_SYNTHETIC_REUSE_TRACE_AND_ONE_POLICY_POINT_ONLY**
