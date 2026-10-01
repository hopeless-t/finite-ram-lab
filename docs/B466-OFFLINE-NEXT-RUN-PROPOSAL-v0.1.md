# B466 — Offline Next-Run Proposal v0.1

Status: **NEXT-RUN LEARNER / PROPOSAL ONLY**.

## 1. Purpose

B465 demonstrated the first bounded GitHub Actions PROBE.

B466 performs the step that was intentionally forbidden inside B465:

> read the completed telemetry and update the next experiment choice.

The temporal boundary is the experiment.

B466 runs only after B465 is frozen.

## 2. Source evidence

B465 observed:

- tile_rows 64 -> 32;
- exact semantics 4/4;
- peak signs mixed: 2 negative / 1 positive / 1 zero;
- median peak delta = -2 KiB;
- median latency ratio = 1.01584;
- effect classification = PEAK_EFFECT_UNRESOLVED_WITH_LATENCY_COST.

The source telemetry digest is carried into every proposal.

## 3. Bounded proposal rule

v0.1 intentionally implements one narrow rule.

When:

1. the source schema is exactly the frozen B465 result;
2. all semantic pairs matched;
3. the changed variable was exactly tile_rows 64 -> 32;
4. the effect was unresolved;
5. absolute median peak delta is <= 1 MiB;
6. median latency ratio is > 1.0;

then propose the opposite side of the already-frozen envelope:

`tile_rows 64 -> 128`.

Everything else goes to:

`HOLD_FOR_MANUAL_REVIEW`.

This is not a learned universal policy. It is a first next-run proposal rule.

## 4. No execution

The output explicitly carries:

- status = PROPOSAL_ONLY;
- execute_now = false;
- requires_new_frozen_decision = true.

B466 cannot execute the proposal.

A later bounce must freeze a new decision receipt before any physical run.

## 5. Why this matters

The application loop now has a clean temporal split:

```text
run N decision
-> run N intervention
-> run N telemetry
STOP

later:
run N telemetry
-> offline proposal
STOP

later:
proposal
-> new frozen decision
-> run N+1
```

This prevents post-outcome adaptation from being confused with a predeclared
treatment.

## 6. Claim ceiling

**OFFLINE_NEXT_RUN_PROPOSAL_ONLY**

B466 does not establish that tile_rows=128 is better.

It establishes that the research application can consume prior evidence and emit
a bounded, provenance-linked next experiment without executing it.

## 7. Next edge

B467 may freeze the B466 proposal into a new PROBE decision and execute the
64 -> 128 comparison.

That would complete one full multi-run feedback loop:

`decision -> intervention -> telemetry -> offline proposal -> new decision -> new intervention`.
