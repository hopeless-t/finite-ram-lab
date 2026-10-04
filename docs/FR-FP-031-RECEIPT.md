# FR-FP-031 Receipt

Status: **PASS / HOSTED PHYSICAL RISK-AWARE GOVERNOR QUALIFIED**

Parent: **FR-FP-030**

- workflow run: 37194869837
- job: 111414535269
- execution head: 4cbfb59828079796336e26b26d2d71882dc5d687
- state size: 8 MiB
- current-run baseline estimator: TWO_PROBE_MIN
- external policy:
  - lambda = 1.0 ms/MiB
  - deadline = 25 ms
  - miss tolerance = 5%

## Current-run physical calibration

COLD probe 1:
- pre-resident fraction: 0
- restore: 3.618 ms

COLD probe 2:
- pre-resident fraction: 0
- restore: 3.299 ms

Chosen baseline:

    b = 3.299 ms

Calibration total:

    6.917 ms

## Risk-aware reuse ceiling

Using the reused residual and WARM priors:

- conditional expected COLD-WARM penalty: 5.285 ms
- conditional deadline miss probability at 25 ms: 3.33%
- cost reuse ceiling: 1.0
- deadline reuse ceiling: 1.0
- combined reuse ceiling: 1.0

Thus this fast current-run regime and explicit policy permit COLD even at
reuse probability 1.0.

## Fixed 10% Governor comparator

- WARM opportunities: 100
- COLD opportunities: 20
- COLD restores: 3
- residency integral: 800 MiB-opportunity
- total restore latency: 21.355 ms
- storage reads: 24 MiB
- drift alarm: opportunity 65

## Risk-aware Governor

- WARM opportunities: 5
- COLD opportunities: 115
- COLD restores: 17
- residency integral: 40 MiB-opportunity
- total restore latency: 63.417 ms
- storage reads: 136 MiB
- drift alarms: 65 / 82 / 101 / 116
- final tier: COLD

Physical ALWAYS_COLD comparator:
- residency integral: 0
- total restore latency: 63.783 ms
- storage reads: 136 MiB

Interpretation:

The dynamic policy moved strongly toward COLD because the current runner was
fast enough that neither expected-cost nor deadline-risk policy restricted reuse.

This is the intended behavior of the explicit risk surface, not a regression.

However, a new redundancy was exposed:

    when reuse ceiling == 1,
    reuse evidence cannot change the WARM/COLD decision.

The drift alarm therefore repeatedly invalidated evidence that was
decision-irrelevant, followed by immediate requalification.

Theory update:

**DO_NOT_KEEP_AN_EVIDENCE_PLANE_RESIDENT_WHEN_THE_CURRENT_DECISION_SURFACE_DOES_NOT_DEPEND_ON_IT**

Next:

Compile and qualify a decision-relevance gate:
- if p_ceiling == 1, bypass reuse qualification and reuse-drift monitoring;
- otherwise retain the qualified reuse-evidence lifecycle.

Claim ceiling:

**HOSTED_PHYSICAL_RISK_AWARE_TIER_ACTUATION_ON_ONE_SYNTHETIC_REUSE_TRACE_AND_ONE_POLICY_POINT_ONLY**
