# FR-FP-029 — Reuse drift-alarm Pareto frontier

Status: **SYNTHETIC DRIFT-FRONTIER CANDIDATE**

Parent: **FR-FP-028**

## Why

FR-FP-028 showed that a naive rolling confidence bound forgets stale evidence
quickly but falsely revokes a stable low-reuse qualification far too often.

The next step is not to choose another arbitrary rolling window.

Instead, expose the recency alarm as a multi-objective frontier.

## Alarm family

Keep the FR-FP-028 recent window:

    35 observations

After a state has already been qualified by the cumulative exact reuse upper
bound, watch the recent reuse count.

Alarm when the last 35 observations contain at least:

    k = 3 / 4 / 5 / 6 / 7 / 8

reuse events.

The alarm does not itself certify COLD.

It only invalidates old evidence and forces requalification.

## Evaluation

Condition on trajectories that are cumulatively qualified after the first 60
observations with true reuse p=0.02.

Then measure three axes.

### Stable false revocation

Keep p=0.02.

Measure the probability that an alarm fires during the next 60 observations.

Lower is better.

### Drift detection coverage

Inject:

    p = 0.15 / 0.25 / 0.50

Measure the fraction of qualified trajectories whose old evidence is invalidated
within 60 observations.

Higher is better.

### Drift detection delay

Among detected drifts, measure the median number of observations until alarm.

Lower is better.

## Reference

The cumulative exact upper bound remains in the panel as a baseline comparator.

This prevents an alarm from looking good merely because it is being compared
only with the rejected naive rolling-UCB rule.

## No universal threshold

Increasing k should:

- reduce stable false revocation;
- reduce weak-drift detection coverage;
- increase weak-drift detection delay.

That is a real policy tradeoff.

The code therefore emits a Pareto set rather than selecting one universal k.

External policy can later specify:

- tolerated false revocation;
- required drift-detection coverage;
- maximum detection delay.

## North-Star consequence

Evidence now has a lifecycle:

    qualify
      -> remain resident while valid
      -> detect evidence-contract drift
      -> invalidate
      -> requalify

That same lifecycle can later be applied to compiled decision skills and other
cached sufficient state.

## Claim ceiling

**SYNTHETIC_DRIFT_ALARM_FRONTIER_FOR_ONE_REUSE_CEILING_AND_WINDOW_ONLY**
