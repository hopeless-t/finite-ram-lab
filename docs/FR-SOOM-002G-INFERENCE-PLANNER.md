# FR-SOOM-002G — Inference-Informed Deadline Planner

Status: **SYNTHETIC CLOSED-LOOP QUALIFICATION**

## Goal

FR-SOOM-002F can infer cross-action dependence from observable outcome traces
without latent BAD labels.

FR-SOOM-002G closes the loop.

Historical trace inference now selects the future pressure-relief policy.

The central question becomes:

> Does observable dependence evidence improve future deadline-safe task
> survival, rather than merely classify traces correctly?

## Historical inference

The planner reuses the FR-SOOM-002F analyzer.

It receives no latent BAD label.

Frozen history classifications are:

- INDEPENDENT history -> IID_COMPATIBLE;
- SHARED_BAD history -> CROSS_ACTION_DEPENDENCE_EVIDENCE.

## Future episode model

Each regime is evaluated on 8192 fresh synthetic future episodes.

Three clustered cooperative actions each have exactly 82 late episodes.

A fourth action, DISTINCT_SPARE, is a frozen differently-coupled 1000-MiB
relief source.

All four actions normally contribute 1000 MiB.

Required relief:

`3000 MiB`.

Therefore the cooperative plan tolerates one clustered late action but not two
or more simultaneous clustered late actions.

This creates real redundancy only when clustered actions do not fail together.

## Policies

### NAIVE_COOPERATIVE

Always uses cooperative redundancy.

It does not consume dependence evidence.

### DEPENDENCE_AWARE

- IID_COMPATIBLE -> keep cooperative redundancy;
- CROSS_ACTION_DEPENDENCE_EVIDENCE -> select BACKGROUND_SACRIFICE.

The synthetic background-sacrifice plan:

- provides 3500 MiB by deadline;
- has semantic loss 73;
- preserves the current task.

### KILL_FIRST

Immediately sacrifices the active task.

Frozen semantic loss:

`280`.

This remains the fast destructive control.

## Reliability rule

A plan qualifies only if:

- deadline-success point rate >= 0.999;
- Wilson 95% lower bound >= 0.999.

## Frozen result — independent future regime

The cooperative cluster has only one multi-action coincidence in 8192 future
episodes.

Both NAIVE_COOPERATIVE and DEPENDENCE_AWARE therefore remain on cooperative
redundancy.

Result:

- deadline failures: 1;
- deadline success: 8191/8192 = 0.99987793;
- Wilson95 lower: 0.99930881;
- reliability qualified: yes;
- current-task losses: 1;
- mean semantic loss: 10.03418;
- p99 semantic loss: 10.

The dependence-aware policy does not escalate unnecessarily.

## Frozen result — shared future regime

The same marginal late count is concentrated into 82 shared episodes.

### NAIVE_COOPERATIVE

- deadline failures: 82;
- deadline success: 8110/8192 = 0.98999023;
- Wilson95 lower: 0.98759321;
- reliability qualified: no;
- current-task losses: 82;
- mean semantic loss: 12.80273;
- p99 semantic loss: 290.

### DEPENDENCE_AWARE

Historical dependence evidence selects BACKGROUND_SACRIFICE.

- deadline failures: 0;
- deadline success: 1.0;
- Wilson95 lower: 0.99953129;
- reliability qualified: yes;
- current-task losses: 0;
- mean semantic loss: 73;
- p99 semantic loss: 73.

### KILL_FIRST

- deadline failures: 0;
- current-task losses: 8192;
- mean semantic loss: 280;
- p99 semantic loss: 280.

## Primary finding

The shared-regime naive policy has lower **mean** semantic loss than the
dependence-aware policy:

`12.80 < 73`.

But it fails the deadline-reliability constraint and its p99 semantic loss
jumps to 290 because rare misses force active-task sacrifice.

The dependence-aware policy pays more expected cost to buy tail safety:

`mean cost up, p99 loss down, current-task survival up`.

Therefore:

`expected semantic loss alone is not a sufficient control objective`.

A constrained planner is more appropriate:

```text
minimize expected semantic loss
subject to:
  deadline reliability >= target
  current-task loss within policy bound
```

## Why this is a step toward an earlyoom successor

The controller is no longer:

```text
pressure threshold
   -> victim score
   -> kill
```

The synthetic architecture is now:

```text
historical shadow receipts
   -> observable dependence inference
   -> failure-domain model
   -> deadline-aware policy selection
   -> cooperative redundancy OR background sacrifice
   -> active-task kill only as emergency fallback
```

That is qualitatively different from a userspace OOM killer.

It is becoming a semantic, risk-constrained memory governor.

## Important non-claim

All future action costs and outcomes are synthetic.

The background-sacrifice plan is not a recommended host configuration.

The 0.999 reliability target is a research threshold.

No live process is controlled.

## Claim ceiling

**SYNTHETIC_INFERENCE_INFORMED_PLANNING_ONLY**

## Next

FR-SOOM-002H should introduce **regime drift**.

Historical dependence may become stale.

A controller that permanently trusts an old failure-domain graph could
over-escalate long after the workload changes.

The next experiment should compare:

- static historical inference;
- sliding-window inference;
- confidence decay / hysteresis.

The endpoint should measure both:

- delayed detection after a regime changes;
- unnecessary destructive escalation after the regime recovers.

That is the next step toward a continuously adapting replacement daemon.
