# FR-FP-032 — Decision-relevance bypass

Status: **HOSTED PHYSICAL DECISION-RELEVANCE CANDIDATE**

Parent: **FR-FP-031**

## Why

FR-FP-031 exposed a new kind of waste.

The current-run calibration produced:

    reuse ceiling = 1.0

That means every possible reuse probability:

    0 <= p <= 1

already satisfies the reuse constraint.

Reuse evidence therefore cannot change the WARM/COLD decision.

Yet the evidenceful Governor still:

- appended reuse observations;
- recomputed exact upper bounds;
- monitored the recency alarm;
- invalidated evidence repeatedly;
- briefly returned WARM after every alarm;
- immediately requalified COLD.

The evidence plane was valid code but decision-irrelevant state.

## Gate

If:

    p_ceiling >= 1

then:

    reuse probability cannot disqualify COLD

and the Governor may compile the policy to:

    BYPASS_REUSE_EVIDENCE_AND_KEEP_COLD

No reuse history is needed.

No Clopper-Pearson update is needed.

No reuse drift alarm is needed.

## Hosted comparison

Use the same frozen FR-FP-030 reuse trace.

Compare:

EVIDENCEFUL_P1_GOVERNOR
: the FR-FP-031 lifecycle with reuse ceiling 1.0.

DECISION_RELEVANCE_BYPASS_P1
: immediately enact the mathematically equivalent unconstrained COLD policy and
  never instantiate the reuse-evidence plane.

Both restore every reuse event and verify byte integrity.

Latency superiority is not a PASS gate.

The target is policy equivalence with less decision machinery and less
evidence-induced WARM residency.

## Meta consequence

The same principle applies above memory tiering:

> keep an observation, model, skill, or council step resident only while it can
> still change an admissible decision.

This is a general route for reducing context and control-plane friction.

## Claim ceiling

**HOSTED_PHYSICAL_P1_REUSE_CEILING_DECISION_RELEVANCE_BYPASS_ONLY**
