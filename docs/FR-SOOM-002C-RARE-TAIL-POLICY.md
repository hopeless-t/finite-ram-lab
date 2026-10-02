# FR-SOOM-002C — Rare-Tail Semantic OOM Policy

Status: **SYNTHETIC MONTE CARLO QUALIFICATION**

## Goal

FR-SOOM-002B introduced response time as a memory-control resource.

FR-SOOM-002C removes the unrealistic assumption that every action has one fixed
latency and one fixed relief value.

The central hypothesis is:

`mean-fast != tail-safe`.

A cooperative action can have an average completion time below the safety
deadline while rare slow responses still make the plan unsuitable for emergency
memory relief.

## Frozen episode

- required relief: 3000 MiB;
- response deadline: 200 ms;
- 8192 deterministic Monte Carlo replicates per plan;
- qualification requires both:
  - point deadline-success rate >= 0.99;
  - Wilson 95% lower bound >= 0.99.

The random stream is hash-derived from the frozen domain
`FR-SOOM-002C-v0.1`, so the reference vector is reproducible without relying on
runtime PRNG state.

## Plans

### MEAN_COOPERATIVE

- Chrome trim + idle-renderer release;
- model shrink;
- indexer graceful exit.

Nominal semantic loss:

`9`

Hard kills:

`0`

The plan is attractive under frozen mean latency and semantic cost.

Its problem is the injected rare latency and under-relief tail.

### TAIL_AWARE_MIXED

- smaller/faster Chrome cache trim;
- batch hard kill;
- indexer graceful exit.

Nominal semantic loss:

`14`

Hard kills:

`1`

The plan intentionally accepts slightly higher semantic loss in exchange for
substantially more deadline margin.

### KILL_FIRST

- active Chrome hard kill.

Nominal semantic loss:

`280`

Current task is destroyed.

This is the fast/destructive control arm.

## Frozen result

| plan | deadline success | Wilson95 lower | mean latency | p95 | p99 | semantic loss | hard kills | current task |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| MEAN_COOPERATIVE | 7525/8192 = 0.918579 | 0.912459 | 190.26 ms | 310 ms | 495 ms | 9 | 0 | survives |
| TAIL_AWARE_MIXED | 8168/8192 = 0.997070 | 0.995644 | 100.69 ms | 118 ms | 120 ms | 14 | 1 | survives |
| KILL_FIRST | 8192/8192 = 1.000000 | 0.999531 | 19.97 ms | 25 ms | 25 ms | 280 | 1 | lost |

The mean-cooperative plan's average completion time is below the 200-ms
deadline, yet its p95 and p99 completion times exceed the deadline by a large
margin.

It therefore fails the frozen 99%-class reliability requirement.

The tail-aware mixed plan pays five additional synthetic semantic-loss points
and one background hard kill, but qualifies the 99%-class reliability floor
while preserving the current task.

## Failure decomposition

For the frozen mean-cooperative plan:

- deadline misses and relief misses are recorded separately;
- the first specimen of each class is retained;
- each specimen carries the per-action tail/under-relief draws.

This is important because:

`late enough relief != insufficient relief`.

They require different repairs.

## Control interpretation

The planner should not optimize only:

`expected semantic loss`

or only:

`expected completion latency`.

A more appropriate constrained form is:

```text
minimize expected semantic loss
subject to:
  P(relief before deadline) >= reliability target
  current-task damage within policy bound
```

In a later real controller the probability model must come from target-host
evidence, not these injected synthetic distributions.

## Connection to Finite RAM Rare-event methodology

The experiment deliberately reuses three existing lab habits:

1. **rare-event capture** — low-frequency slow/under-relief outcomes are retained;
2. **failure-state biopsy** — deadline miss and relief miss are separate states;
3. **confidence-bound qualification** — the point rate alone is not sufficient.

This prevents a visually attractive average from qualifying an unsafe tail.

## Important non-claim

The injected tail probabilities and latency ranges are synthetic controls.

No claim is made that a real Chrome trim, systemd pressure callback, cgroup
reclaim, or service exit has these timings.

The 200-ms deadline is not a recommended host setting.

No live process is controlled.

## Claim ceiling

**SYNTHETIC_RARE_TAIL_POLICY_ONLY**

## Next

Two useful continuations now become possible.

### FR-SOOM-002D — correlated pressure/action failure

The current action tails are independent.

Real pressure episodes can correlate failures:

- scheduler contention;
- swap congestion;
- reclaim storms;
- I/O stalls;
- CPU saturation.

A shared BAD pressure state could make several cooperative actions become slow
at once.

That would connect directly to FR-CLM-001E's matched-marginal / different-risk-
shape result.

### Target-host shadow statistics

When a matching MVCA/LDC operator binding exists, the read-only SOOM-002 shadow
can start collecting the real ingredients needed to replace these synthetic
priors.
