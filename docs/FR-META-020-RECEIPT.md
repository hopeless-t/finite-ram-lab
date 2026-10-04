# FR-META-020 Receipt

Status: **PASS / DECISION-RELEVANCE PRUNING SKILL QUALIFIED**

Parent: **FR-META-019**

Final qualification:
- workflow run: 37203697984
- job: 111440399722
- execution head: 161cbe1302677682ab8f50c40b400d843928f31c
- full decision-skill tests: PASS
- catalog resident-budget gate: PASS (<30%)

Evidence:
- FR-FP-031 / PR #151
- FR-FP-032 / PR #152

Compiled skill:

    PRUNE_IRRELEVANT_REUSE_EVIDENCE

Trigger:

    risk_surface_qualified = true
    reuse_can_change_tier_decision = false

Action:

    SKIP_REUSE_EVIDENCE_AND_DRIFT_MONITORING

Invalidation:
- reuse becomes decision-relevant;
- qualified risk surface is invalidated.

## Self-hosted budget failure and repair

First qualification attempt:
- workflow 37195539681
- new skill behavior: PASS
- catalog budget: FAIL
- observed fraction: 0.320319 > frozen 0.30 limit

Rejected repairs:
- do not relax the 30% limit;
- do not inflate the source-history denominator;
- do not remove evidence provenance, maturity, or invalidation semantics.

Repair:
- evict repeated resident metadata fields `kind` and `replications`;
- those fields do not participate in trigger matching, priority ordering,
  emitted capsules, invalidation, or primary-action selection.

The repaired catalog passed the original frozen budget.

Compiled lesson:

**EVICT_DECISION_IRRELEVANT_METADATA_BEFORE_EXPANDING_A_RESIDENT_SKILL_BUDGET**

Scope discipline:

This receipt does not yet promote a universal cross-domain pruning skill.
Only reuse-evidence pruning has hosted physical qualification.

Next:

Replicate decision-relevance pruning in an independent decision plane before
generalizing the meta-rule.

Claim ceiling:

**COMPILED_DECISION_IRRELEVANT_REUSE_EVIDENCE_BYPASS_ONLY**
