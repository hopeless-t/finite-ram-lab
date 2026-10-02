# FR-SOOM-002F — Observable-Only Failure-Domain Inference

Status: **SYNTHETIC TRACE-INFERENCE QUALIFICATION**

## Goal

FR-SOOM-002E showed that a multi-signal detector can distinguish a synthetic
shared BAD state with far fewer false escalations than PSI alone.

However, it still used the generator's BAD label to fit the detector.

A real Semantic OOM controller will not have that label.

FR-SOOM-002F therefore removes latent state from the analyzer entirely.

The analyzer receives only:

- episode identity;
- whether each cooperative action was late or timely.

The question is:

> Can shared failure-domain evidence be recovered from observed co-failure
> structure alone?

## Frozen traces

Two synthetic corpora contain 16,384 episodes and three actions.

Every action is late in exactly 164 episodes in both corpora.

Therefore marginal tail prevalence is exactly matched.

### INDEPENDENT

Each action gets its own deterministic set of 164 late episodes.

### SHARED_BAD

All three actions are late in the same 164 episodes.

The analyzer is not told which corpus it is observing.

## Observable statistic

For every action pair, count how many episodes make both actions late.

Then sum those pairwise co-failure counts.

Observed values:

- INDEPENDENT: 5;
- SHARED_BAD: 492.

The analyzer also records pairwise phi coefficients and the count of episodes
with two or more simultaneous late actions.

## Null calibration

The null uses 999 deterministic independent circular shifts.

For every permutation:

- each action trace is shifted independently;
- exact marginal tail count is preserved;
- within-action trace shape is preserved;
- cross-action alignment is destroyed.

This makes the null appropriate for the specific question:

`is the observed cross-action alignment stronger than expected when each action's own trace is preserved?`

The analyzer never receives a latent BAD label.

## Frozen result

| metric | INDEPENDENT | SHARED_BAD |
|---|---:|---:|
| tail count per action | 164 | 164 |
| pair co-failure total | 5 | 492 |
| multi-action late episodes | 5 | 164 |
| mean pairwise phi | 0.000154 | 1.000000 |
| null p95 pair co-failures | 9 | 9 |
| null p99 pair co-failures | 11 | 11 |
| permutation upper p | 0.587 | 0.001 |
| classification | IID_COMPATIBLE | CROSS_ACTION_DEPENDENCE_EVIDENCE |

## Interpretation

The independent trace lands comfortably inside its own permutation-calibrated
null.

The shared trace is far outside the null despite having exactly the same
per-action marginal tail counts.

Therefore:

`marginal failure prevalence alone does not identify failure-domain structure`.

And, within this frozen synthetic control:

`shared failure-domain evidence can be recovered from observable co-failure traces without latent labels`.

The term `IID_COMPATIBLE` is deliberately weak.

Failure to reject dependence is not proof of independence.

## Controller implication

This gives the future Semantic OOM controller a route to learn a correlation
graph from ordinary shadow receipts.

A candidate offline flow becomes:

```text
read-only shadow receipts
        |
        v
per-action timely/late traces
        |
        v
pairwise co-failure + permutation calibration
        |
        v
failure-domain evidence graph
        |
        v
planner avoids counting correlated actions as independent redundancy
```

This can operate before any live intervention is enabled.

## Why this helps an earlyoom successor

An emergency killer sees a pressure threshold and a victim set.

A semantic resource controller should additionally know whether its supposedly
independent pre-kill remedies are actually coupled.

If cache trim, reclaim, and graceful background exit all fail together under the
same substrate pressure, firing all three does not provide three independent
chances of relief.

FR-SOOM-002F provides a way to estimate that coupling from observations rather
than declarations.

## Important non-claim

The traces are synthetic.

The permutation threshold is not a real-host escalation threshold.

The result does not prove that Linux action failures have this structure.

No live process is controlled.

## Claim ceiling

**SYNTHETIC_OBSERVABLE_DEPENDENCE_INFERENCE_ONLY**

## Next

FR-SOOM-002G should feed inferred dependence back into the planner.

Compare:

- a NAIVE planner that treats cooperative actions as independent redundancy;
- a DEPENDENCE_AWARE planner that discounts actions from the same inferred
  failure domain and reserves a differently-coupled fallback.

The key endpoint should not be classifier accuracy alone.

It should be:

`deadline-safe semantic loss after inference-informed planning`.
