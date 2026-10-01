# B474 — Multi-q 95% Rank-Coverage Expansion v0.1

Status: **SPEND FROZEN 33-RUN CALIBRATION BUDGET**.

## 1. Goal

B473 established that a sample-max rank coverage floor of 95% requires at least
19 comparable observations per q.

Current counts before B474:

- q1 = 20
- q2 = 8
- q4 = 8
- q7 = 8

B474 spends exactly the frozen experiment budget:

- q2: +11
- q4: +11
- q7: +11

Total:

`33 fresh-process observations`.

## 2. Execution order

Eleven three-q rounds are frozen.

The order rotates among q2/q4/q7 so no q is permanently first or last.

Every physical observation runs in a fresh process.

## 3. Hard gates

Each observation must preserve exact numerical semantics.

All q values must produce one shared final output digest.

Any semantic mismatch blocks coverage interpretation.

## 4. Pooled coverage

After B474, each of q2/q4/q7 has:

`4 B469 + 4 B471 + 11 B474 = 19`

comparable observations.

Therefore, under the explicit exchangeability assumption:

```text
rank-max one-step coverage floor
= 19/20
= 95%
```

q1 already has n=20, corresponding to 20/21 ~= 95.238%.

## 5. Empirical maximum update

For each q, B474 compares the new 11-run maximum against the prior union maximum.

If the maximum moves, the new larger value is preserved.

The 95% rank statement attaches to the updated pooled empirical maximum, not to
the older boundary.

## 6. Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_MULTI_Q_CALIBRATION**

This remains vulnerable to non-exchangeable environment/workload drift and is not
a worst-case guarantee.

## 7. Next

B475 should build a coverage-aware governor v1 whose peak thresholds are the
updated pooled empirical maxima and whose decision receipt exposes:

- sample count;
- rank coverage floor;
- source provenance;
- explicit exchangeability assumption.

That will replace the vague `observed_upper` label with a quantified risk
contract.
