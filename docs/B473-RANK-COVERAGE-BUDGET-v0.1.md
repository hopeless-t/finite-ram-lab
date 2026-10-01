# B473 — Rank-Coverage Sample Budget v0.1

Status: **OFFLINE EXPERIMENT-BUDGET PLANNER**.

## 1. Question

B472 attached a 95.238% one-step rank-max coverage floor to q=1 because q=1 now
has 20 comparable fresh-process observations.

The other q values have only eight each.

B473 asks:

> How many additional comparable observations are required before every q can
> carry a declared sample-max rank coverage target?

## 2. Rank-max sample formula

Under the explicit exchangeability assumption:

```text
coverage_floor(n) = n / (n + 1)
```

To require:

```text
n/(n+1) >= p
```

we need:

```text
n >= p/(1-p)
```

rounded upward to an integer.

Examples:

- target 95% -> n >= 19
- target 99% -> n >= 99

These are one-step predictive rank bounds, not worst-case guarantees.

## 3. Current comparable sample counts

q=1:

- B469 4
- B471 4
- B472 12
- total = 20
- floor = 20/21 ~= 95.238%

q=2, q=4, q=7:

- B469 4
- B471 4
- total = 8 each
- floor = 8/9 ~= 88.889%

## 4. Frozen 95% sample budget

Required per q:

`19`

Additional samples:

- q1: 0
- q2: 11
- q4: 11
- q7: 11

Total additional physical observations:

`33`

## 5. Why this matters

The experiment scheduler now has a quantitative reason to spend runs.

It is no longer:

> "collect more data because more is safer."

It is:

> "collect exactly enough comparable observations to reach a declared
> exchangeability-conditional rank coverage class."

This turns experimental confidence into a resource-budget decision.

## 6. Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_SAMPLE_BUDGET**

The formula does not protect against distribution shift, runner drift, changed
workload geometry, or non-exchangeable execution conditions.

## 7. Next

B474 should spend the frozen 33-run budget:

- q2: +11
- q4: +11
- q7: +11

with balanced execution order.

After B474, every q should have at least n=19 comparable observations and can
carry a 95%-class sample-max rank coverage floor, conditional on exchangeability.
