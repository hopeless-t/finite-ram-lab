# Durable semantic state vs resident compute

Status: research crossover candidate

Source intake: https://note.com/npaka/n/n341b20a052c6

## Why this belongs in Finite RAM Lab

Always-on agent designs expose the same resource distinction this lab studies elsewhere:

```text
must remain durable
!=
must remain resident
!=
must remain actively computing
```

For agentic workloads the durable object may be a small Commitment state while the expensive planner/model/context can be evicted, reconstructed, or fetched only when an event requires it.

## Resource decomposition

```text
D = durable semantic bytes
R = resident working-set bytes
C = active compute cost
W = reconstruction / wake cost
lambda = event rate
```

A naive always-resident design pays approximately for `R + continuous C` even during idle periods.

A dormant design retains `D`, then pays `W + task compute` on relevant wakes.

The research question is not "sleep is always cheaper." It is:

> At what event rate, reconstruction cost, state size, latency target, and memory pressure does durable-state / ephemeral-compute dominate always-resident execution?

## Candidate experiment

Create synthetic agent workloads with equal semantic behavior but different residency policies:

1. always-resident planner state;
2. serialized Commitment + reconstructed planner context;
3. tiered hot/cold semantic state;
4. event-driven wake plus periodic audit fallback.

Measure:

- peak/steady resident memory;
- bytes required for durable state;
- wake latency;
- reconstruction bytes and CPU time;
- total compute while idle;
- event-to-effect latency;
- duplicate/recovery work after process death.

Sweep event arrival rate and state-reconstruction cost to find the residency knee.

## Boundary

This is a systems/resource hypothesis, not evidence that a particular agent framework is inefficient. It should reuse Finite RAM Lab's rule:

> prove the state before interpreting the outcome.

The key candidate principle is:

> **Persist meaning; earn residency.**