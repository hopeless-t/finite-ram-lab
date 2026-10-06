# FR-P9-008 — Online Joint Replan Under Finite PSS Admission

## Motivation

FR-P9-007 measured all six `N={1,2,4} × {KEEP_WARM,FAULT_IN}` arms on one hosted Linux surface and found that all six remained non-dominated on the typed objective set. That makes one thing explicit: a joint plan cannot be treated as timeless merely because its semantic workload is unchanged.

FR-P9-008 asks a narrower question:

> If the planner has a valid same-surface measurement frontier and a finite PSS admission cap, what must happen when the planner-relevant resource facts change between idle and work?

## Contract

A plan is bound to two independent certificates:

1. **resource certificate** — hashes only planner-relevant resource facts (`pss_cap_kib`, capability availability), not observation epoch or notes;
2. **measurement certificate** — hashes the measured six-arm decision surface, including PSS, resume/work/tail metrics and semantic job digests.

This gives the following admission rule:

```text
same resource certificate + same measurement certificate
    -> RESOURCE_PLAN_VALID_AUTHORITY_STILL_REQUIRED

resource certificate changed
    -> REPLAN_REQUIRED

measurement certificate changed
    -> REMEASURE_OR_REPLAN_REQUIRED

no feasible candidate
    -> FAIL CLOSED
```

Observation freshness is therefore not itself a reason to replan.

## Frozen adversary

The hosted P9-007 measurement surface is reused as the candidate set. The admission cap transition is synthetic:

```text
t0: 50,000 KiB cap
    -> N4:KEEP_WARM peak ~= 47 MiB is admissible

t1: same cap, new observation epoch
    -> certificate unchanged; no replan

t2: 40,000 KiB cap
    -> both N4 arms exceed the hard cap
    -> stale plan rejected
    -> online replan selects the highest still-admissible concurrency class
    -> N2:KEEP_WARM

t3: capability unavailable
    -> no feasible plan
    -> fail closed
```

The service-policy tie break used by this falsifier is explicit and external:

`HIGHEST_ADMISSIBLE_CONCURRENCY_CLASS_THEN_LOWEST_RESUME`

It is not a universal recommendation to maximize workers. Hard resource feasibility is applied first, and `scalar_gain = null` remains unchanged.

## Semantic invariant

Every arm must carry the same deterministic job digest map before it is admitted into the candidate set. The replan must preserve that map exactly.

This separates:

```text
semantic equivalence
    !=
resource feasibility
    !=
service-policy preference
    !=
execution authority
```

## Measurement-drift adversary

A resource certificate alone is insufficient. If the measured PSS/latency surface changes while the cap remains the same, a plan must not silently continue using stale evidence. FR-P9-008 therefore binds the measurement surface into the plan and requires `REMEASURE_OR_REPLAN_REQUIRED` on evidence drift.

## Claim ceiling

`HOSTED_FR_P9_007_MEASUREMENT_ANCHOR_PLUS_SYNTHETIC_PSS_CAP_TRANSITION_ONLY_NO_PHYSICAL_GLOBAL_PRESSURE_OR_UNIVERSAL_POLICY_CLAIM`

The 50,000 -> 40,000 KiB transition is an admission-contract adversary, not a physical host-memory-pressure experiment.

## Next falsifier

Replace the synthetic cap transition with an isolated physical pressure domain (for example a bounded quota/cgroup-like surface where available) and test whether observed online replans match the certificate model without changing semantic results.
