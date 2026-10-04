# FR-FP-032 Receipt

Status: **PASS / HOSTED PHYSICAL DECISION-RELEVANCE BYPASS QUALIFIED**

Parent: **FR-FP-031**

- workflow run: 37195187519
- job: 111415470551
- execution head: 1482be29a324f720cf24893190734614996bd39f
- reuse ceiling under test: 1.0
- frozen reuse schedule: FR-FP-030/031 120-opportunity trace
- restore count: 17

Qualified law:

    if reuse_ceiling >= 1:
        reuse probability cannot change COLD eligibility
        -> skip reuse evidence collection
        -> skip reuse upper-bound updates
        -> skip reuse drift alarms
        -> keep COLD

## Evidenceful p=1 Governor

- WARM opportunities: 5
- COLD opportunities: 115
- COLD restores: 17
- drift alarms: 65 / 82 / 101 / 116
- policy-event lower bound: 124
- residency integral: 40 MiB-opportunity
- storage reads: 136 MiB

## Decision-relevance bypass

- WARM opportunities: 0
- COLD opportunities: 120
- COLD restores: 17
- reuse evidence observations: 0
- reuse-upper evaluations: 0
- drift-alarm evaluations: 0
- drift alarms: 0
- residency integral: 0 MiB-opportunity
- storage reads: 136 MiB
- final tier: COLD

All restores verified exactly.

The bypass preserves the physical COLD restore behavior required by the decision
surface while removing the control-plane state that cannot affect that decision.

Decision:

**PRUNE_THE_REUSE_EVIDENCE_PLANE_WHEN_THE_RISK_SURFACE_MAKES_REUSE_DECISION_IRRELEVANT**

Meta transfer:

An observation, model, skill, council step, or monitor should remain resident
only while it can still change an admissible decision.

Claim ceiling:

**HOSTED_PHYSICAL_P1_REUSE_CEILING_DECISION_RELEVANCE_BYPASS_ONLY**
