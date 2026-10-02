# FR-SOOM-002B — Deadline-Constrained Action Ladder

Status: **SYNTHETIC ACTION-PLANNER QUALIFICATION**

## Goal

FR-SOOM-002A showed that existing Linux memory-control systems already expose
both halves of a stronger controller:

- pressure detection and emergency termination;
- cooperative application-side shrinking.

FR-SOOM-002B asks what happens when those actions compete under a strict
response-time bound.

The objective is not "never kill".

It is:

`minimize semantic loss per required pressure relief, subject to a response deadline`.

## Frozen pressure episode

Required relief:

`3000 MiB`

Frozen response deadlines:

`25, 100, 200, 600 ms`

The fixture exposes several classes of intervention:

- cache trimming;
- idle-renderer removal;
- service/workload shrinking;
- graceful restartable exit;
- checkpoint-and-exit;
- hard kill.

Only one action tier may be selected for each workload.

Selected actions are modeled as concurrent, so response latency is the maximum
selected action latency.

This is a synthetic planning model, not a timing claim about real software.

## Kill-first baseline

The emergency baseline chooses:

`CHROME_KILL`

Frozen characteristics:

- relief = 3200 MiB;
- response latency = 20 ms;
- semantic loss = 280;
- current task does not survive.

This is deliberately analogous to the failure mode that motivated Semantic OOM.

## Semantic planner objective

Lexicographic objective:

1. minimize current-task damage;
2. minimize semantic loss;
3. minimize hard kills;
4. minimize excess relief;
5. minimize action count;
6. deterministic name tie-break.

The response deadline is a hard feasibility constraint.

## Frozen result

| deadline | selected plan | relief | semantic loss | hard kills | current task |
|---:|---|---:|---:|---:|---|
| 25 ms | model kill + batch kill + indexer kill | 3500 MiB | 73 | 3 | survives |
| 100 ms | Chrome cache trim + batch kill + indexer graceful exit | 3200 MiB | 14 | 1 | survives |
| 200 ms | Chrome cache+idle-renderer trim + model shrink + indexer graceful exit | 3000 MiB | 9 | 0 | survives |
| 600 ms | Chrome cache trim + terminal trim + model shrink + batch checkpoint/exit | 3000 MiB | 3 | 0 | survives |

## Primary finding

More response time expands the feasible intervention set.

In the frozen fixture:

```text
25 ms
  -> only destructive background actions can meet the target cheaply

100 ms
  -> one hard kill remains, but cooperative relief starts to dominate

200 ms
  -> no hard kill is required

600 ms
  -> a lower-loss cooperative/checkpoint plan becomes feasible
```

The result is not "slow is always better".

The actual controller must trade:

`hang risk from waiting`

against:

`semantic loss from escalating too early`.

That is the new control variable.

## Design implication

The replacement architecture should likely expose an **escalation budget**:

```text
pressure state
    |
    +-- remaining relief deficit
    +-- remaining response-time budget
    +-- available reversible actions
    +-- semantic cost of irreversible actions
```

At each step the planner chooses whether another reversible action can still
complete before the safety deadline.

This is closer to deadline-aware scheduling than to a single victim score.

## Relation to existing OSS

systemd's Resource Pressure Handling provides a standardized route for
application-side pressure reactions such as cache release, idle worker
termination, and GC.

Meta oomd provides a detector/action policy-engine precedent.

Linux cgroup v2 provides memory.high and memory.reclaim as useful shaping and
proactive-reclaim primitives.

FR-SOOM's novel question is how to combine such mechanisms with current-task
semantic cost under an explicit deadline.

## Important non-claim

All latency, relief, and semantic-loss values are synthetic.

No live browser, service, or process is controlled.

The result does not establish a safe waiting time under real memory pressure.

## Claim ceiling

**SYNTHETIC_DEADLINE_ACTION_LADDER_ONLY**

## Next

The next step should be to replace fixed action latencies with distributions and
rare tails.

For each action class, model:

- relief uncertainty;
- completion-latency distribution;
- timeout probability;
- semantic-loss distribution.

Then ask whether a policy that is optimal on mean latency becomes unsafe under
p95/p99 response tails.

That connects the Semantic OOM lane directly back to Finite RAM Lab's Rare-event
methodology.
