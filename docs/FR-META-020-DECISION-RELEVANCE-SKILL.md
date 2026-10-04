# FR-META-020 — Compile decision-relevance pruning

Status: **DECISION-SKILL COMPILATION CANDIDATE**

Parent: **FR-META-019**

Evidence:
- FR-FP-031 / PR #151
- FR-FP-032 / PR #152

## Qualified pattern

FR-FP-031 produced a qualified risk surface with:

    reuse ceiling = 1

At that boundary, reuse probability cannot change COLD eligibility.

The evidenceful Governor nevertheless continued to:
- collect reuse history;
- recompute exact upper bounds;
- evaluate drift alarms;
- invalidate and recreate evidence epochs.

FR-FP-032 physically qualified the compiled bypass:

    SKIP_REUSE_EVIDENCE_AND_DRIFT_MONITORING

while preserving the required all-COLD policy and exact restore integrity.

## Skill

Trigger:

    risk_surface_qualified = true
    reuse_can_change_tier_decision = false

Action:

    SKIP_REUSE_EVIDENCE_AND_DRIFT_MONITORING

Invalidation:

- reuse becomes decision-relevant;
- the qualified risk surface is invalidated.

## Scope discipline

This skill is deliberately narrower than the general philosophical rule:

> prune every decision-irrelevant plane.

Only the reuse-evidence case has hosted physical qualification here.

A broader cross-domain skill requires an independent replication in another
decision plane.

## Resident-budget contract

The existing decision-skill catalog must remain below its frozen 30% source
history budget.

The budget is not relaxed merely because a new skill is useful.

## Claim ceiling

**COMPILED_DECISION_IRRELEVANT_REUSE_EVIDENCE_BYPASS_ONLY**


## Resident-budget failure biopsy

The first META-020 implementation correctly selected the new pruning skill, but
the self-hosted catalog gate failed:

    catalog_fraction_of_source = 0.320319

The frozen limit remains:

    < 0.30

Rejected repair:

- do not relax the 30% budget;
- do not inflate SOURCE_HISTORY_CHARACTERS;
- do not delete evidence provenance, maturity, or invalidation conditions.

Compression repair:

The resident SKILLS table repeated two metadata fields for every skill:

    kind
    replications

Neither field participates in:

- trigger matching;
- priority ordering;
- emitted decision capsules;
- invalidation;
- primary action selection.

They are therefore evicted from the resident executable catalog.

This is the same Finite RAM rule applied to the skill compiler itself:

> metadata that cannot affect the current executable decision should not consume
> the hot catalog budget.

The evidence PRs, maturity and invalidation conditions remain resident.
