# FR-META-019 Receipt

Status: **PASS / CALIBRATION ROUTING AND NEGATIVE-RESULT CI REPAIR SKILLS QUALIFIED**

Parent: **FR-META-018**

Final qualification:
- workflow run: 37191957184
- job: 111405857354
- execution head: 5a02fe871dd13562e1a4dae68a1d7f3746c294aa
- full suite: 616 tests
- result: PASS
- decision-skill catalog resident-budget gate: PASS (<30% of frozen source history)

## Compiled calibration frontier

Skill:

    COLD_RESTORE_CALIBRATION_FRONTIER

Trigger scope:
- COLD restore baseline question;
- qualified 8 MiB fixture;
- cross-run restore prior available.

Compiled action:

    ONE_PROBE_BASELINE
      -> OPTIONAL TWO_PROBE MIN IF WORTH COST
      -> KEEP TAIL PRIOR

This deliberately keeps the external value-of-information judgment outside the
compiled skill.

## Compiled negative-result guard

Skill:

    NEGATIVE_RESULT_INVALIDATES_REJECTED_CI_GATE

Action:

    REMOVE_REJECTED_SHAPE_FROM_CI_GATE_BEFORE_CHILD_QUALIFICATION

This was compiled from the FR-FP-016 / FR-FP-018 incident where theory correctly
rejected monotonic COLD-size behavior while an old executable PASS gate still
required it.

## Self-hosted catalog-budget failure

The first FR-META-019 implementation caused the decision-skill catalog to exceed
its own <30% resident-surface limit:

    32.824%

The first compression reduced this to:

    30.028%

still above the frozen gate.

The budget was not relaxed and the denominator was not inflated.

Overlapping calibration decisions were compressed into one frontier capsule and
redundant metadata was shortened until the existing resident-budget contract
passed.

Compiled lesson:

**WHEN_THE_SKILL_CATALOG_HITS_ITS_OWN_RESIDENT_BUDGET, COMPRESS_OVERLAPPING_DECISIONS_BEFORE_EXPANDING_THE_BUDGET**

Decision:

**COMPILE_CALIBRATION_ROUTING_AND_NEGATIVE_RESULT_CI_REPAIR_WITHIN_THE_EXISTING_SKILL_RESIDENT_BUDGET**

Claim ceiling:

**COMPILED_CALIBRATION_ROUTING_AND_NEGATIVE_RESULT_CI_CONTRACT_REPAIR_ONLY**
