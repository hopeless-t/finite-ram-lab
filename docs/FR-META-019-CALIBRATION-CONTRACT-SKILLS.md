# FR-META-019 — Compile restore calibration and negative-result CI repair

Status: **DECISION-SKILL COMPILATION CANDIDATE**

Parent: **FR-META-018**

Core evidence:
- FR-FP-021 / PR #140
- FR-FP-022 / PR #141
- FR-FP-016 negative result / PR #135
- FR-FP-018 downstream CI-contract repair / PR #137

## Skill 1 — current-run COLD baseline calibration

When all facts are explicit:

- question concerns current-run COLD restore baseline;
- state size is the qualified 8 MiB fixture;
- the FR-FP-020-style cross-run prior is available;

compile to:

    USE_ONE_PROBE_BASELINE_KEEP_TAIL_PRIOR

The tail prior is deliberately retained.

Baseline calibration and isolated deadline-miss risk are different states.

## Skill 2 — optional precision

If the same facts hold and an external decision explicitly states:

    extra baseline precision justifies one additional probe

compile to:

    USE_TWO_PROBE_LOWER_ENVELOPE_KEEP_TAIL_PRIOR

The second probe is not enabled merely because it exists.

The value/cost judgment remains external to the skill evidence.

## Skill 3 — negative result repairs the executable contract

A failure found during FR-FP-018 showed that FR-FP-016 had correctly rejected a
monotonic COLD-size law in documentation while an old CI PASS gate still
required monotonic COLD latency.

Compile the meta-rule:

    qualified negative result
    + CI still requires rejected shape
      ->
    REMOVE_REJECTED_SHAPE_FROM_CI_GATE_BEFORE_CHILD_QUALIFICATION

A theory update is not complete until executable qualification stops enforcing
the rejected theory.

## Why this is meta-meta improvement

The research loop now updates:

1. its physical model;
2. its decision policy;
3. the tests that decide whether the updated model is valid.

This prevents stale executable assumptions from slowing or corrupting future
bounces.

## Claim ceiling

**COMPILED_CALIBRATION_ROUTING_AND_NEGATIVE_RESULT_CI_CONTRACT_REPAIR_ONLY**
