# MEMCG-003 Seven-Slot Eviction Result v1

> **Status:** PASS / REJECT_K7_SLOT_MODEL / MEASUREMENT CONTAMINATION EXPOSED
> **Canonical run:** `36459951576`
> **Launch commit:** `6cb688d7c8578ce95e217e83adcb7249a3555efa`
> **Aggregate artifact id:** `10987225468`
> **Aggregate digest:** `sha256:25430aad2b5b5761ead7a15e3ab242bde7dbb10cbec29be77d00eea188331d64`
> **Duplicate run:** `36459972685` — noncanonical by pre-result rule; excluded from model selection.

## Preregistered decision

`REJECT_K7_SLOT_MODEL`

Support blocks:

`0 / 4`

Observed DISTINCT_CHURN first-event thresholds:

`[2, 1, 4, 2]`

Derived primary model selection:

- modal threshold: 2
- median threshold: 2
- best K by absolute error: 2
- Bayesian posterior mode: K=2
- posterior P(K=2): 0.8854545641

Leave-one-block-out trained K:

`[2,2,2,2]`

This is a valid result for the implemented preregistered detector.

## Critical control failure

The first-event detector was defined as either:

- target stock drop; or
- target probe fresh recharge.

But the target was deliberately touched once after every challenger/control step.

That probe consumes one cached page whenever target stock remains present.

Control arms therefore developed +64 recharge events even without distinct-memcg churn.

Per-block control event counts:

### SAME_MEMCG_ACTIVITY

`[1,1,1,1]`

### NO_CHURN

`[1,1,2,1]`

### SIX_ONLY

`[2,1,2,3]`

Thus the primary first-event threshold is not an uncontaminated estimate of seven-slot eviction capacity.

## Exact event decomposition

### DISTINCT_CHURN

block0:
- m2: +64 recharge
- m3: 63-page stock drop +64 recharge
- m7: 60-page stock drop +64 recharge

block1:
- m1: +64 recharge
- m2: 63-page stock drop +64 recharge
- m3: 125-page stock drop +64 recharge
- m5: 62-page stock drop +64 recharge

block2:
- m4: +64 recharge
- m6: 62-page stock drop +64 recharge

block3:
- m2: +64 recharge
- m7: 59-page stock drop +64 recharge
- m8: 63-page stock drop +64 recharge

### NO_CHURN

Fresh +64 recharge appeared in every block despite no challenger insertion.

One no-churn block also showed a 64-page stock drop.

### SAME_MEMCG_ACTIVITY

All four blocks showed a fresh +64 target recharge at some probe count, while no large target stock-drop event occurred.

This is direct evidence that repeated target probing itself consumes the hidden stock state.

## Stock-drop-only diagnostic

Removing probe-recharge events from the threshold definition is not a preregistered repair, but it is a useful diagnostic.

First target stock-drop >=16 pages:

- DISTINCT_CHURN: `[3,2,6,7]`
- SIX_ONLY: `[5,None,1,4]`
- SAME_MEMCG_ACTIVITY: `[None,None,None,None]`
- NO_CHURN: `[None,None,7,None]`

This suggests distinct memcg churn has a real effect beyond same-memcg activity, but the threshold is not cleanly seven because the target CPU/cache is still exposed to uncontrolled churn and the target was repeatedly consumed by the observer.

## Interpretation

MEMCG-003 rejects the **implemented observable K=7 threshold model**.

It does **not** justify the stronger statement that Linux's source-level `NR_MEMCG_STOCK=7` structure is absent.

Instead the experiment exposed two measurement problems:

1. **destructive observation** — the target probe consumes cached stock;
2. **control-plane interference** — orchestration and unrelated memcg activity can compete for the same per-CPU shared cache.

The next experiment must remove both before retesting the source-level seven-slot prediction.

## pmndrs/math consequence

MATH-002 remains useful as a secondary structural lens.

For this contaminated run its proper use is diagnostic:
- control response clouds overlap the +64 recharge axis;
- geometry cannot rescue K=7;
- hull overlap is expected evidence of measurement contamination.

The geometric lens should be rerun on the repaired non-consuming experiment for substantive model comparison.

## Authority boundary

Hosted Linux accounting research only.
No local-PC execution.
No memory-control policy.
