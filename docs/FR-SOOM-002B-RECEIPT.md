# FR-SOOM-002B — Deadline Action Ladder Qualification Receipt

Status: **PASS / SYNTHETIC DEADLINE-AWARE ACTION PLANNER VALIDATED**

## Frozen qualification

- workflow run: 37012492073
- job: 110855331309
- execution head: adc17af53c4a39a86802fda0c771f21de614929a
- targeted tests: 7/7 PASS
- artifact ID: 11228761304
- artifact ZIP SHA256: 9b9cd2b7adf591533f0a1f3884b616dcdde6b840cb0d76fdd58737ddc519fcce
- spec SHA256: 47d238f22a8252abcc9e1b8ae13b1ff527f90ea9515b242f82c4ad881ac39682
- result SHA256: dea86bfe1afa75e554cb0c22e0246f6566778912003c273a2b12e078a84eaad7

## Frozen episode

Required pressure relief:

`3000 MiB`

Kill-first baseline:

- action: CHROME_KILL
- relief: 3200 MiB
- response latency: 20 ms
- semantic loss: 280
- current task survives: false

## Deadline-dependent semantic plans

| deadline | plan | relief | semantic loss | hard kills | current task |
|---:|---|---:|---:|---:|---|
| 25 ms | model kill + batch kill + indexer kill | 3500 MiB | 73 | 3 | survives |
| 100 ms | Chrome cache trim + batch kill + indexer graceful exit | 3200 MiB | 14 | 1 | survives |
| 200 ms | Chrome cache+idle-renderer trim + model shrink + indexer graceful exit | 3000 MiB | 9 | 0 | survives |
| 600 ms | Chrome cache trim + terminal trim + model shrink + batch checkpoint/exit | 3000 MiB | 3 | 0 | survives |

## Primary result

In the frozen fixture, allowing more response time monotonically expands the
available low-loss intervention set.

The hard-kill count drops:

`3 -> 1 -> 0 -> 0`

while semantic loss drops:

`73 -> 14 -> 9 -> 3`.

The result therefore introduces a new state variable for Semantic OOM:

`remaining response-time budget`.

A victim score alone cannot represent this tradeoff.

## Control interpretation

The planner state should eventually include:

- current pressure severity;
- remaining relief deficit;
- remaining response-time budget;
- available reversible relief;
- completion-risk estimates;
- semantic cost of irreversible actions.

The escalation question becomes:

> Is there still enough time for another lower-loss action to complete before
> the safety deadline?

This is different from both a static victim ranking and a fixed sequence of
actions.

## Relation to existing systems

The experiment intentionally combines architecture already visible in the
ecosystem:

- PSI-style pressure observation;
- application-side cooperative release;
- cgroup/workload shaping;
- graceful restartable exit;
- emergency termination.

The experimental contribution is the deadline-aware semantic objective, not the
existence of these primitives.

## Important non-claim

All action latencies, relief quantities, and semantic-loss values are synthetic.

The 25/100/200/600-ms points are not host-safe thresholds.

No live process was signaled or controlled.

No browser reclaim API was invoked.

## Claim ceiling

**SYNTHETIC_DEADLINE_ACTION_LADDER_ONLY**

## Next

FR-SOOM-002C should replace fixed action values with deterministic stochastic
distributions and Rare-event tails.

The central question is:

`mean-fast action != tail-safe action?`

For each action class, estimate or inject:

- completion-latency distribution;
- relief distribution;
- timeout / non-response probability;
- correlated failure state;
- p95 / p99 semantic outcome.

A planner that looks best on mean latency may become unsafe once rare slow
responses are included.
