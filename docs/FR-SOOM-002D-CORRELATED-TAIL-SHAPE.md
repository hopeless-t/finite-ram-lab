# FR-SOOM-002D — Correlated Tail Risk Shape

Status: **SYNTHETIC MATCHED-MARGINAL QUALIFICATION**

## Goal

FR-SOOM-002C showed:

`mean-fast != tail-safe`.

FR-SOOM-002D asks a second question:

> If every action has the same marginal probability of becoming slow, does the
> controller risk remain the same when those slowdowns are correlated?

The frozen hypothesis is:

`matched marginal action tails != matched controller risk shape`.

## Experimental control

Three cooperative actions jointly provide exactly 3000 MiB of relief:

- Chrome shrink: 1500 MiB;
- model shrink: 600 MiB;
- indexer exit: 900 MiB.

Their normal latency is below the 200-ms deadline.

Their tail latency is above it.

The panel contains 16,384 replicates.

Each action is assigned **exactly 164 tail replicates** in both arms:

`164 / 16384 = 0.010009765625`.

This is an exact finite-sample marginal match, not merely an approximate
Bernoulli match.

## Arms

### INDEPENDENT

Each action gets an independently hash-ranked set of 164 tail replicates.

The finite-sample marginal count for every action is therefore fixed.

### SHARED_BAD

One shared set of 164 replicates puts all three actions into tail state at once.

Again, each individual action has exactly 164 tail replicates.

Only the cross-action dependence structure changes.

## Frozen result

| metric | INDEPENDENT | SHARED_BAD |
|---|---:|---:|
| per-action tail count | 164 each | 164 each |
| affected episodes | 484 | 164 |
| affected rate | 0.029541 | 0.010010 |
| deadline success rate | 0.970459 | 0.989990 |
| multi-action tail episodes | 8 | 164 |
| conditional mean tail-action count | 1.016529 | 3.000000 |
| conditional p95 tail-action count | 1 | 3 |
| conditional mean relief deficit | 1016.53 MiB | 3000 MiB |
| conditional p95 relief deficit | 1500 MiB | 3000 MiB |
| conditional max relief deficit | 2400 MiB | 3000 MiB |

## Primary result

The shared BAD arm affects **fewer** pressure episodes because the same action
tail events are concentrated into the same replicates.

But when the shared state hits, the damage is much deeper:

- all three actions are late;
- the full 3000-MiB relief target is absent at the deadline;
- every affected shared-BAD episode is a multi-action failure.

Therefore it would be wrong to summarize the shared arm as simply "safer"
because its deadline-success rate is higher.

The risk has been redistributed:

`broad + shallow != narrow + deep`.

This is the same structural lesson that appeared in the semantic-trajectory
lane, now expressed as cross-action memory-controller risk.

## Why this matters for a real Semantic OOM controller

A controller that assumes action outcomes are independent can overestimate the
value of diversification.

For example, several cooperative actions may all depend on the same constrained
substrate:

- CPU scheduling;
- swap or storage I/O;
- reclaim progress;
- allocator locks;
- memory bandwidth;
- a shared pressure-notification path.

If the substrate enters a BAD state, "try several cheap actions in parallel"
may not provide independent chances of success.

The planner therefore needs a notion of **failure domain** in addition to action
cost and latency.

Possible future action metadata:

```text
action
  relief distribution
  latency distribution
  semantic cost
  failure domain
  correlation group
```

## Methodological transfer

The result reinforces a general Finite RAM rule:

`prevalence != severity != mechanism`.

A lower affected rate is not automatically a better controller outcome if the
conditional deficit tail becomes much worse.

## Important non-claim

The shared BAD state is synthetic.

No claim is made that Linux currently produces this exact dependence pattern.

No live process is controlled.

The experiment does not establish that independent or correlated action tails
are universally preferable.

## Claim ceiling

**SYNTHETIC_CORRELATED_TAIL_RISK_SHAPE_ONLY**

## Next

FR-SOOM-002E should turn the shared BAD state into a small latent pressure-state
model and test whether it can be inferred from observations.

Candidate observable inputs:

- PSI slope / level;
- reclaim progress;
- swap-in / swap-out velocity;
- refault rate;
- action response latency;
- relief achieved by deadline.

The key question becomes:

> Can the controller detect that multiple apparently independent actions are
> currently inside one shared failure domain early enough to escalate?
