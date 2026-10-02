# FR-SOOM-002H — Regime Drift and Hysteresis

Status: **SYNTHETIC ADAPTATION QUALIFICATION**

## Goal

FR-SOOM-002G established a closed loop from observed dependence to future policy.

A long-running daemon introduces a new problem:

`historical truth can become stale`.

If a controller permanently trusts old dependence evidence, it can keep
sacrificing background work after the workload has recovered.

If it reacts to every window immediately, one short anomalous burst can cause
unnecessary escalation and policy churn.

FR-SOOM-002H isolates that tradeoff.

## Frozen regime sequence

Twelve observation/control windows:

```text
0 IID
1 IID
2 one-window correlated BURST
3 IID
4 SHARED
5 SHARED
6 SHARED
7 SHARED
8 IID recovery
9 IID
10 IID
11 IID
```

Each window contains 2048 episodes.

Each clustered action has exactly 20 late outcomes per window.

The controller does not receive the regime labels.

They exist only for harness scoring.

## Window evidence

Each window runs an observable co-failure test with 199 deterministic circular
shift permutations.

Frozen evidence sequence:

```text
IID
IID
DEPENDENCE
IID
DEPENDENCE
DEPENDENCE
DEPENDENCE
DEPENDENCE
IID
IID
IID
IID
```

The isolated burst is therefore strong enough to look like a shared failure
domain for one window.

That is intentional.

## Strategies

### STATIC_INITIAL

Never changes from cooperative mode.

This is the stale-belief / no-adaptation baseline.

### RAW_SLIDING

The immediately previous window decides the next window.

This reacts quickly, but a one-window burst spills into the following IID
window.

### HYSTERESIS_2_ENTER_1_EXIT

- require two consecutive DEPENDENCE windows before entering background
  sacrifice;
- leave background sacrifice after one IID-compatible window.

This is intentionally asymmetric.

Entering destructive mode requires confirmation; returning to cooperative mode
is allowed quickly.

## Frozen result

| metric | STATIC | RAW_SLIDING | HYSTERESIS |
|---|---:|---:|---:|
| current-task losses | 101 | 41 | 61 |
| unnecessary background-sacrifice windows | 0 | 2 | 1 |
| plan switches | 0 | 4 | 2 |
| sustained-SHARED detection delay | never | 1 window | 2 windows |
| recovery release delay | 0 | 1 window | 1 window |
| post-burst stale escalation | no | yes | no |
| mean semantic loss | 11.15072 | 36.71712 | 26.44499 |
| p99.9 semantic loss | 290 | 290 | 290 |

## Primary finding

There is no free winner.

RAW_SLIDING protects the current task sooner after sustained dependence begins,
but it also overreacts to the isolated burst and switches policy four times.

HYSTERESIS removes the burst spillover, cuts policy switches from four to two,
and halves unnecessary background-sacrifice windows from two to one.

The price is slower entry into protective mode:

- RAW detection delay: 1 window;
- HYSTERESIS detection delay: 2 windows.

This yields:

`stability x responsiveness x semantic preservation`

as another controller tradeoff.

## Important mean-vs-tail lesson

STATIC has the lowest mean semantic loss in this synthetic sequence because
background sacrifice is expensive and active-task losses are rare.

But it also loses the current task 101 times.

Again:

`low expected cost != acceptable tail behavior`.

All three strategies still expose a p99.9 semantic-loss tail of 290.

Regime adaptation reduces catastrophic-event frequency; it does not eliminate
the emergency tail.

## Earlyoom-successor implication

A persistent semantic memory governor now needs **belief lifecycle** in addition
to pressure response.

Candidate state:

```text
failure-domain evidence
  confidence
  age
  consecutive confirmations
  last contradictory evidence
  current intervention mode
```

That suggests a daemon architecture closer to an adaptive control system than a
threshold-triggered killer.

## Important non-claim

All windows, costs, and regime changes are synthetic.

No hysteresis count or observation window is proposed for a real host.

No strategy is globally ranked as best.

No live process is controlled.

## Claim ceiling

**SYNTHETIC_REGIME_DRIFT_CONTROL_ONLY**

## Next

FR-SOOM-002I should stop treating observation windows as equal-duration batches.

A real daemon receives asynchronous evidence.

The next lane should model:

- event-time pressure observations;
- confidence decay with wall-clock time;
- deadline urgency;
- burst arrival rate;
- intervention cooldown.

That moves the design from batch adaptation toward an actual daemon state
machine.


## Qualification correction

The scratch pilot used abstract action identifiers `A/B/C` as part of the
deterministic hash domains.

The committed harness uses the canonical action identifiers:

- `CHROME_CACHE`;
- `MODEL_SHRINK`;
- `INDEXER_EXIT`.

Because draw-domain identity is part of a deterministic stochastic fixture, the
IID overlap specimens differ even though all marginal tail counts and control
parameters are unchanged.

The committed stream yields:

- STATIC current-task losses: 101;
- RAW_SLIDING: 41;
- HYSTERESIS: 61.

No evidence threshold, strategy rule, tail count, or regime sequence was changed.

The evidence sequence and the primary stability/responsiveness conclusion remain
unchanged.
