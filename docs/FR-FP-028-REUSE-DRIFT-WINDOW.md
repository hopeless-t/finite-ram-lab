# FR-FP-028 — Reuse evidence staleness and rolling-window negative result

Status: **SYNTHETIC DRIFT NEGATIVE-RESULT CANDIDATE**

Parent: **FR-FP-027**

## Why

FR-FP-027 gives an exact evidence budget only while the Bernoulli reuse rate is
stable.

A workload can change after qualification.

If old low-reuse evidence is retained forever, cumulative confidence can become
stale.

A natural repair is to use only a recent rolling window.

FR-FP-028 tests that repair before adopting it.

## Frozen synthetic fixture

Decision reuse ceiling:

    0.10

Confidence:

    95%

Low-reuse phase:

    p = 0.02
    60 observations

Then inject:

    p = 0.15 / 0.25 / 0.50
    for 60 observations

Compare:

CUMULATIVE
: exact one-sided Clopper-Pearson upper bound over all observations.

ROLLING
: the same exact bound over the most recent 35 observations.

The 35-sample window is large enough to certify p <= 0.10 when it contains zero
reuse events.

## Two goals

### Drift response

Among trajectories qualified by both methods at the drift point, measure how
many post-drift observations are needed before:

    p_upper > 0.10

### Stable false revocation

Run a control where p remains 0.02 for all 120 observations.

Among trajectories qualified at observation 60, measure how often each method
later revokes qualification even though no drift occurred.

## Desired lesson, not desired winner

Rolling evidence is expected to react faster because it forgets old evidence.

That does not automatically make it a better default.

The experiment explicitly checks the cost of that forgetting.

## North-Star consequence

If cumulative is stale but rolling is too noisy, the next mechanism should not
be another arbitrary window size.

The correct next question becomes:

> what evidence-lifecycle or change-detection rule invalidates old evidence
> only when there is evidence of a workload transition?

That keeps knowledge resident while valid and evicts it when its validity
contract breaks.

## Claim ceiling

**SYNTHETIC_BERNOULLI_DRIFT_INJECTION_FOR_ONE_10PCT_REUSE_CEILING_ONLY**
