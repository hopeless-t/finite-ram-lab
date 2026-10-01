# B470 — Budget-Aware q Governor v0.1

Status: **SOFTWARE GOVERNOR OVER OBSERVED FRONTIER**.

## 1. Goal

B469 produced the first exact physical q frontier.

B470 turns that frontier into an application decision without inventing one
universal "best q".

The user/runtime supplies a peak-memory budget.

The governor chooses the lowest observed median latency among exact candidates
that fit that budget.

## 2. No weighted score

The rule is:

```text
minimize observed median latency
subject to:
  observed peak model <= peak budget
  exact semantic gate passed
```

Memory and latency are not combined with arbitrary alpha/beta weights.

## 3. Two risk modes

### median

Use the measured median normalized peak for each q.

This is the research-facing central estimate.

### observed_upper

Use the maximum normalized peak observed across the four B469 repetitions.

This is a more conservative dogfood mode.

It is still only an empirical upper observation from four runs, not a certified
worst-case bound.

## 4. Median-policy breakpoints

Observed B469 median peaks:

- q=1: 67,014,656 B
- q=2: 67,024,896 B
- q=4: 71,217,152 B
- q=7: 71,507,968 B

Therefore the v0.1 median policy is:

```text
budget < 67,014,656 B
  -> no measured q fits

67,014,656 <= budget < 67,024,896
  -> q=1

67,024,896 <= budget < 71,217,152
  -> q=2

71,217,152 <= budget < 71,507,968
  -> q=4

budget >= 71,507,968
  -> q=7
```

Relative to q=1 median peak, the q transitions require approximately:

- q2: +10 KiB;
- q4: +4.01 MiB;
- q7: +4.29 MiB.

## 5. Observed-upper policy

Observed maximum peaks:

- q=1: 67,022,848 B
- q=2: 67,108,864 B
- q=4: 71,303,168 B
- q=7: 71,507,968 B

This shifts the small-budget q2 threshold upward.

That difference is intentional: risk appetite is part of the runtime contract.

## 6. Why q=2 matters

In B469, q=2 delivered about 3.31% lower median work time than q=1 for only
+10 KiB median normalized peak.

B470 does not call q=2 universally optimal.

It says:

> q=2 becomes the selected operating point whenever the declared peak budget can
> admit q2 but not the higher-q candidates.

That is a constraint-defined optimum.

## 7. App shape

The CLI can now be used as:

```text
source q frontier
+ risk mode
+ peak budget
-> selected q decision
```

This is the first directly usable Finite Frontier Governor component.

## 8. Claim ceiling

**OBSERVED_FRONTIER_CONSTRAINT_GOVERNOR_V0**

The policy is valid only relative to the B469 hosted observations.

It must be re-learned for another workload/runtime/environment.

## 9. Next

B471 should dogfood the governor inside GitHub Actions:

1. declare several peak budgets;
2. let B470 select q;
3. execute the selected q;
4. compare observed peak against the budget contract;
5. freeze any budget miss as a governor calibration event.

That will turn the observed frontier into a closed-loop resource governor.
