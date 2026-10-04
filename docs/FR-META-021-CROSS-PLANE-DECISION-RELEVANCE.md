# FR-META-021 — Cross-plane decision-relevance capsule

Status: **META-META GENERALIZATION CANDIDATE**

Parent: **FR-META-020**

Evidence:
- FR-FP-031 / PR #151
- FR-FP-032 / PR #152
- FR-FP-033 / PR #154

## Two independent qualified planes

### Plane A — reuse monitoring

When the qualified risk surface makes:

    reuse ceiling = 1

reuse probability cannot change COLD eligibility.

Qualified action:

    prune reuse history
    prune reuse upper-bound updates
    prune reuse drift monitoring

### Plane B — calibration measurement

With the qualified TWO_PROBE_MIN baseline estimator:

    probe 2 can only keep or lower the baseline

If probe 1 already gives:

    reuse ceiling = 1

probe 2 cannot make reuse decision-relevant.

Qualified action:

    stop calibration after probe 1

The fifteen-run leave-one-run-out backtest found:
- 2 safe early-stop runs;
- 0 unsafe early stops;
- 4 runs where probe 2 really changed the surface.

Therefore the rule is not "always measure less".
It is "stop only after decision irrelevance is proven".

## Meta-meta compression

FR-META-020 used a domain-specific resident skill:

    PRUNE_IRRELEVANT_REUSE_EVIDENCE

FR-META-021 replaces it with one normalized capsule:

    PRUNE_PROVEN_DECISION_IRRELEVANT_WORK

Domain-specific proof is compiled into deterministic fact derivation.

The resident skill catalog therefore does not need one new LLM-facing rule per
decision plane.

## Normalized proof contract

The generic capsule requires:

    decision_irrelevance_proven = true
    skip_preserves_admissible_decision = true

Two deterministic adapters currently establish those facts:

1. qualified reuse risk surface + reuse cannot change tier decision;
2. qualified TWO_PROBE_MIN calibration + first probe already produces reuse
   ceiling 1.

If neither proof holds, fail closed and keep the work plane.

## Safety boundary

This capsule does not authorize arbitrary skipping.

It only prunes work after a domain proof establishes that skipping preserves
the admissible decision.

Authority remains separate.

## Resident-budget contract

Skill count does not increase.

The domain-specific reuse skill is replaced by one cross-plane capsule.

The existing frozen catalog budget remains <30%.

## Claim ceiling

**CROSS_PLANE_DECISION_RELEVANCE_PRUNING_FOR_REUSE_MONITORING_AND_SECOND_COLD_CALIBRATION_PROBE_ONLY**
