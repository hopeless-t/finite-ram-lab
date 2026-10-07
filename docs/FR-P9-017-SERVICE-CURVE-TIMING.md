# FR-P9-017 — Equal service budget, different arrival time

## Why

FR-P9-016 showed that fixed wall-clock slack is better represented by resource-specific delivered service than by duration alone. It also exposed a requested-duty versus observed-delivery gap.

But a scalar *total* service budget may still be too weak for deadline-sensitive residency decisions.

FR-P9-017 asks whether **when** service arrives matters even when nominal and observed total CPU-yield/CPU-busy budgets are comparable.

## Frozen physical shape

Every FAULT_IN child is pinned to one CPU and receives a 60 ms post-release scheduling window containing nominally:

- 30 ms CPU-yield time;
- 30 ms same-CPU busy time.

The order changes:

- `FRONT_YIELD`: yield first, then busy;
- `BACK_YIELD`: busy first, then yield;
- `INTERLEAVED`: three yield/busy pairs.

The reconstructed capability is required by a **30 ms subdeadline**. The experiment records a counterfactual readiness miss:

`deadline_miss = max(0, reconstruct_done - deadline)`

Semantic work runs after the complete 60 ms observation window, so all lanes can still verify identical semantic output without changing their service schedule after a miss.

## Preregistered falsifier

PASS requires all of the following without threshold movement:

- semantic identity and no OOM;
- exact one-CPU affinity;
- reconstruction starts only after phase-A release;
- every FAULT_IN lane preserves >=8 MiB peak saving vs KEEP_WARM;
- observed total busy and yield durations remain comparable across patterns (max/min <=1.25);
- FRONT_YIELD accumulates <=5 ms deadline miss across four transitions;
- BACK_YIELD accumulates >=20 ms deadline miss;
- BACK_YIELD exceeds FRONT_YIELD by >=15 ms.

If total service is comparable but deadline outcomes differ, a scalar service integral is insufficient for this bounded workload.

## Candidate contract

```text
ServiceCurve = (
  resource_kind,
  contention_domain,
  time,
  delivered_service,
  measurement_epoch
)
```

Residency admission can then ask whether sufficient service arrives **before the capability-use deadline**, not merely whether the full horizon contains enough aggregate service.

## Boundary

This remains a GitHub-hosted Linux single-CPU Python-thread/gzip proxy. It does not establish a universal scheduler theorem, universal service curve, or application benchmark. Authority and retry permission remain outside the resource optimizer.
