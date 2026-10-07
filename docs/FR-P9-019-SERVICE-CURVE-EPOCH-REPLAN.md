# FR-P9-019 — Physical service-curve epoch invalidation and replan

## Purpose

FR-P9-018 analytically proved a bounded fail-closed rule: stale service-curve evidence must return `REPLAN_REQUIRED` instead of resource-feasible admission. FR-P9-019 returns to hosted physical evidence and asks whether the guard prevents a stale residency plan from being used after a **controlled** service-arrival-pattern change.

This is deliberately not described as spontaneous host drift. The physical fixture changes from the already-qualified P9-017 `FRONT_YIELD` proxy to `BACK_YIELD` under one-CPU pinning.

## Sequence

```text
epoch e0
FRONT_YIELD physical calibration
    -> FAULT_IN meets 30 ms reconstruction subdeadline
    -> stale candidate plan = FAULT_IN

controlled condition change
    -> observed epoch e1
    -> service arrival becomes BACK_YIELD

unguarded evidence lane
    -> execute stale e0 FAULT_IN at e1
    -> expose deadline miss

guarded lane
    -> compare plan epoch e0 with observed epoch e1
    -> REPLAN_REQUIRED
    -> stale FAULT_IN invocation count = 0
    -> conservative current-epoch fallback = KEEP_WARM
```

The unguarded lane exists only to expose the failure the guard must prevent. It is not the recommended execution path.

## Typed tradeoff

The fallback is intentionally conservative. `KEEP_WARM` should avoid reconstruction-at-deadline risk but pay a materially higher resident-memory peak than `FAULT_IN`. This preserves the Part9 rule that deadline safety and resident memory are separate objective dimensions; no scalar universal winner is claimed.

## Authority boundary

`REPLAN_REQUIRED` is a resource-control result only.

```text
REPLAN_REQUIRED != retry permission
resource-feasible != authority
fallback candidate != invocation authority
```

## Claim ceiling

`HOSTED_GITHUB_LINUX_CONTROLLED_FRONT_TO_BACK_SERVICE_ARRIVAL_SWITCH_PROXY_ONLY_NO_SPONTANEOUS_HOST_DRIFT_OR_UNIVERSAL_SCHEDULER_CLAIM`

## Next gate

After this one-resource epoch gate, compile a typed conjunction over multiple resources without scalarizing their units. Candidate form:

```text
admit iff for every required resource r:
    current_epoch(r)
    and S_r(D_r) >= W_r
```

A first proxy can separate CPU reconstruction service from storage/transfer bytes, then test whether a plan that satisfies one resource curve but not the other correctly fails admission.
