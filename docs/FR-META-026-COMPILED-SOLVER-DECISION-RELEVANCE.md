# FR-META-026 — Prune rich solver rehydration behind a qualified compiled surface

Status: **CROSS-PLANE DECISION-RELEVANCE ADAPTER CANDIDATE**

Parent: **FR-META-025**

Evidence:
- FR-FP-057 / PR #183
- FR-FP-058 / PR #184

## Fifth decision plane

Existing decision-relevance pruning already covers:

1. reuse monitoring;
2. second COLD calibration measurement;
3. physical placement actuation;
4. structural migration-model refit.

FR-FP-058 adds a fifth independently qualified plane:

5. rich solver / optimizer rehydration.

The full eight-path physical evidence and DP/knapsack remain available in cold
storage.

The hot decision surface contains only:

- six physical crossover thresholds;
- seven scalar-supported path IDs;
- explicit invalidation conditions.

The compiled lookup matched direct scoring at 50,020 tested rent points with
zero mismatches after the numerical boundary contract was qualified.

## Deterministic proof adapter

Normalize the solver-specific facts:

    rich_solver_rehydration_question = true
    compiled_surface_qualified = true
    compiled_surface_matches_direct_solver = true
    compiled_surface_valid_for_current_family = true

into:

    decision_irrelevance_proven = true
    skip_preserves_admissible_decision = true

and route through the already-resident capsule:

    PRUNE_PROVEN_DECISION_IRRELEVANT_WORK

No new LLM-facing skill is added.

## Fail closed

Retain the rich solver if:

- direct equivalence is not proven;
- the compiled family is invalidated;
- required proof facts are absent.

Changing external memory rent alone does not invalidate the capsule because rent
is the compiled surface's input.

## Numerical boundary

The compiled surface inherits FR-FP-058's machine-precision crossover contract.

This adapter does not reinterpret or loosen physical policy boundaries.

## Resident-budget contract

Skill count must remain 18.

The executable catalog must remain below the frozen 30% source-history budget.

The budget is not relaxed for this adapter.

## Meta-meta consequence

The control pattern is:

    rich evidence / solver in cold storage
      -> qualified compact decision boundary hot
      -> prune solver rehydration while valid
      -> rehydrate only on validity-contract failure

This is Finite RAM applied to the optimizer itself.

## Claim ceiling

**CROSS_PLANE_DECISION_RELEVANCE_PRUNING_EXTENDED_TO_FP058_COMPILED_SOLVER_REHYDRATION_ONLY**
