# FR-META-024 Receipt

Status: **PASS / INFORMATION-VALUE PRUNING SKILL QUALIFIED WITHIN FROZEN RESIDENT BUDGET**

Parent: **FR-META-023**

Final qualification:
- workflow run: 37219022153
- job: 111485379729
- execution head: afc6cbbda366316fe84daba9740d4567d57b978c
- decision-skill suite: PASS
- catalog resident-budget gate: PASS (<30%)
- resident skill count: 18

Primary evidence:
- FR-FP-044 / PR #168
- FR-FP-045 / PR #169

Compiled skill:

    STOP_LOW_VALUE_INFORMATION_ACQUISITION

Generic trigger:

    information_value_ceiling_proven = true
    acquisition_cost_ge_information_value_ceiling = true

Action:

    STOP_INFORMATION_ACQUISITION_TAKE_ROBUST_ACTION

First proof adapter:

    horizon_measurement_question = true
    robust_information_value_bound_qualified = true
    measurement_cost_ge_information_value_ceiling = true

If acquisition cost remains below the qualified value ceiling, the compiler
fails closed and retains measurement.

## Self-hosted catalog compression

First qualification attempt:
- workflow 37218911680
- behavior tests: PASS
- catalog fraction: 0.3006832405121433
- frozen limit: <0.30
- result: FAIL

The budget was not relaxed.

Compression sequence:
1. compile the overwhelmingly common `mc=SKIP` as an implicit resident default;
2. compile `maturity=QUALIFIED` as an implicit resident default;
3. restore both values explicitly in emitted capsules.

Exceptional MC modes and maturity states remain explicit.

This preserves executable meaning while shrinking repeated resident metadata.

Theory update:

Decision-relevance pruning is not the only safe work-elimination rule.

A task may remain capable of changing a decision yet still be safely skipped
when the maximum value of perfect information cannot repay its acquisition
cost.

Decision:

**STOP_INFORMATION_ACQUISITION_WHEN_A_QUALIFIED_VALUE_CEILING_CANNOT_REPAY_ITS_COST**

Relationship to decision-relevance pruning:
- decision irrelevance is the limiting zero-information-value case;
- the proof contracts remain separate;
- no deeper unification is claimed yet.

Claim ceiling:

**COMPILED_INFORMATION_VALUE_PRUNING_FOR_QUALIFIED_HORIZON_MEASUREMENT_CONTEXT_ONLY**
