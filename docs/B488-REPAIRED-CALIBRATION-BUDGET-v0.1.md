# B488 — Repaired Frontier Calibration Budget v0.1

Status: **EVIDENCE-BUDGET PLANNER FOR THE REPAIRED RUNTIME**.

## 1. Why B488 exists

B487 rebuilt the q frontier after replacing the content-sensitive boolean-index
centering primitive.

The repaired median Pareto set is:

`{q2, q4, q7}`.

q1 is excluded from the production calibration budget because q2 has the same
observed median peak and lower median latency.

The old B475 95%-coverage thresholds belong to the old BOOLEAN_INDEX
implementation and must not be reused.

## 2. Existing repaired evidence

B487 used eight independent GitHub-hosted runner blocks.

Thus every repaired Pareto q currently has:

`n = 8`

independent runner-block observations.

Under the same explicit exchangeability assumption used by the previous
sample-max Governor:

```text
rank-max one-step coverage floor
=
n / (n + 1)
```

so the current repaired frontier carries only:

`8/9 ~= 88.889%`

sample-max rank coverage.

## 3. Target sample counts

To require:

```text
n/(n+1) >= p
```

we need:

```text
n >= p/(1-p)
```

rounded upward.

Therefore:

- 95% requires n >= 19
- 99% requires n >= 99

## 4. Frozen 95% repaired budget

Current n per Pareto q:

- q2 = 8
- q4 = 8
- q7 = 8

Additional independent runner observations required:

- q2 = +11
- q4 = +11
- q7 = +11

Total:

`33`

## 5. Why runner observations, not child-process repetitions

B479-B487 showed that hosted-runner block variation is material at the tens of
KiB scale used by Governor thresholds.

Therefore B488 budgets independent runner-job observations, not multiple child
processes inside one runner VM, as the primary calibration unit.

## 6. Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_REPAIRED_CALIBRATION_BUDGET**

This is not a worst-case memory guarantee.

The coverage statement assumes future repaired-runtime observations are
exchangeable with the comparable hosted-runner calibration population.

## 7. Next

B489 should spend exactly 33 independent repaired-runtime observations:

- q2 +11
- q4 +11
- q7 +11

using order-balanced q execution within each independent runner job.

After B489, each Pareto q should carry at least n=19 and a 95%-class sample-max
rank coverage floor.
