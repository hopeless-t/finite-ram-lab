# B489 — Repaired Runtime 95% Calibration v0.1

Status: **SPEND THE 33-INDEPENDENT-RUNNER CALIBRATION BUDGET**.

## 1. Goal

B488 froze a 33-observation budget for the repaired TILED_WHERE runtime:

- q2 +11
- q4 +11
- q7 +11

B489 spends that exact budget.

## 2. Historical repaired samples

B487 produced eight independent hosted-runner samples for every repaired Pareto q.

Those raw TILED_WHERE samples are frozen in:

`analysis/inputs/B487-REPAIRED-RAW-CALIBRATION-v0.1.json`.

The pooled calibration therefore uses actual per-runner peaks, not B487 medians.

## 3. New runner blocks

B489 launches eleven independent GitHub-hosted jobs.

Every runner block executes one fresh child for:

- q2
- q4
- q7

using the repaired TILED_WHERE implementation, seed469, and size2048.

The q order rotates:

- 2,4,7
- 4,7,2
- 7,2,4

across blocks.

Total new physical observations:

`11 runner blocks x 3 q = 33`.

## 4. Hard semantic gate

Within each block:

- every q must be exact;
- all three q values must emit the same output digest.

Any mismatch blocks calibration.

## 5. Pooled sample-max calibration

For each q:

```text
8 B487 runner samples
+
11 B489 runner samples
=
19 independent hosted-runner samples
```

The pooled empirical maximum is updated from the raw 19 values.

Under the explicit exchangeability assumption:

```text
rank-max one-step coverage floor
=
19/20
=
95%
```

## 6. Why the maximum may move again

B474 previously demonstrated that increasing sample count can move an empirical
maximum even when a small prior panel had no misses.

Therefore B489 treats any new maximum as calibration information, not as a failed
repair.

## 7. Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_REPAIRED_95P_CALIBRATION**

The 95% statement is a one-step rank statement under exchangeability, not a
worst-case RAM guarantee.

## 8. Next

If all q reach n=19 with exact semantics, B490 should build a new
coverage-aware Governor v2 from the repaired q2/q4/q7 empirical maxima.

The old B475 Governor remains tied to the BOOLEAN_INDEX runtime.
