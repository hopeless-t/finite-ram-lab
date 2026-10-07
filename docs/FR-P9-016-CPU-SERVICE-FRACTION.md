# FR-P9-016 — CPU service fraction inside fixed slack

## Why

FR-P9-015 falsified scalar wall-clock slack: 40 ms of CPU-yielding time and 40 ms of same-CPU busy work had essentially the same memory peak but very different reconstruction and exposed-stall cost.

FR-P9-016 asks whether the categorical label can be refined into a quantity the residency compiler can optimize.

## Frozen sweep

The wall-clock slack is fixed at 40 ms per transition. Every process is pinned to exactly one allowed CPU. The main thread applies a 2 ms duty-cycle controller with requested same-CPU busy fractions:

`0%, 25%, 50%, 75%, 100%`

The reconstruction thread, gzip representation, 16 MiB logical capability, 24 MiB phase-A workspace, four transitions, semantic work and high memory quota are otherwise held fixed. Three repetitions reverse lane order on the middle repetition.

## Candidate quantity

A first-order nominal service budget is:

`service_budget = slack_duration * (1 - busy_fraction)`

This is deliberately only a proxy. Python thread scheduling/GIL sharing can still provide reconstruction service during nominally busy intervals, so the experiment records the observed busy fraction and does not claim a universal CPU-share formula.

The more general compiler direction is:

```text
ResourceServiceBudget = (
  resource_kind,
  contention_domain,
  window,
  available_service
)
```

rather than a scalar slack duration.

## Preregistered PASS

PASS requires semantic identity, no OOM, exact single-CPU affinity, post-release reconstruction, >=8 MiB peak saving in every FAULT_IN lane, ordered observed busy fractions, low stall at 0%, material stall at 100%, >=50 ms endpoint reconstruction spread, Pearson correlation >=0.80 for duty vs reconstruction and >=0.70 for duty vs exposed stall, plus at least one interior reconstruction cost strictly between the endpoints.

Thresholds are frozen before hosted measurement. Failure is retained as negative evidence; thresholds are not moved after observation.

## Boundary

This is a GitHub-hosted Linux single-CPU duty-cycle Python-thread/gzip proxy. It is not a universal CPU scheduler, cgroup CPU-share, or application-performance claim. Authority and retry permission remain outside the optimizer.
