# B491 — Repaired Governor v2 Boundary Dogfood v0.1

Status: **BOUNDARY DISPATCH + PHYSICAL COMPLIANCE DOGFOOD**.

## 1. Goal

B490 qualified the repaired-runtime Governor v2.

B491 tests two different things together:

1. does the software choose the correct q exactly at and immediately below each
   calibrated breakpoint?
2. do fresh repaired-runtime executions behave compatibly with the declared 95%
   empirical-max contracts?

## 2. Frozen v2 breakpoints

```text
50,696,192 B -> q2
58,941,440 B -> q4
71,507,968 B -> q7
```

All carry n=19 and 95% sample-max rank coverage.

## 3. Boundary dispatch checks

Every runner block verifies:

- q2 boundary - 1 -> no eligible q
- q2 boundary -> q2
- q4 boundary - 1 -> q2
- q4 boundary -> q4
- q7 boundary - 1 -> q4
- q7 boundary -> q7

Any dispatch mismatch blocks the physical interpretation.

## 4. Physical panel

Eight independent hosted-runner jobs.

Each job runs:

- repaired q2 once
- repaired q4 once
- repaired q7 once

in rotating order.

Total:

`24 fresh physical observations`.

## 5. Exceedance interpretation

A 95%-class empirical maximum is not a hard bound.

B491 therefore does not label one new maximum as immediate failure.

For each q, the count of strict boundary exceedances in the eight-runner future
panel is compared with the same Beta-Binomial reference used by B476:

`BetaBinomial(m=8, alpha=1, beta=19)`.

Three q tests use:

- family alpha = 0.05
- per-q alpha = 0.05/3 ~= 0.01667

Classifications:

- NO_EXCEEDANCE
- TAIL_COMPATIBLE_EXCEEDANCE
- DRIFT_SUSPECT

## 6. Why this is a useful application milestone

The Governor now has an executable contract:

```text
budget
-> q decision
-> physical run
-> compare against declared evidence boundary
-> classify exceedance as ordinary tail or drift suspect
```

This closes the loop from calibration to runtime self-check.

## 7. Claim ceiling

**REPAIRED_GOVERNOR_V2_BOUNDARY_DOGFOOD**

## 8. Next

If B491 is compatible, the repaired Governor can move from research-only
qualification toward the GitHub Actions application/dogfood lane.

If a q is drift suspect, open a targeted recalibration/biopsy lane rather than
silently widening all thresholds.
