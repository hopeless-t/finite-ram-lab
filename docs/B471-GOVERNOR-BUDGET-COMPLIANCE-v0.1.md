# B471 — Governor Budget Compliance Dogfood v0.1

Status: **GOVERNOR-ENFORCED EXECUTION / BOUNDARY CALIBRATION**.

## 1. Goal

B470 can choose q from a measured frontier.

B471 asks the next operational question:

> If the governor chooses q because a measured peak model fits the declared
> budget, does a new fresh-process execution actually remain under that budget?

This is the first dogfood of the governor itself.

## 2. Why test exact breakpoints

The observed-upper B470 policy uses the largest peak seen in four B469 samples.

That is deliberately not called a worst-case guarantee.

B471 stress-tests the four exact observed-upper breakpoints:

- 67,022,848 B -> q=1
- 67,108,864 B -> q=2
- 71,303,168 B -> q=4
- 71,507,968 B -> q=7

If a new run exceeds one of these budgets, the correct outcome is not to hide the
miss. The miss becomes evidence that the empirical peak model needs a safety
margin or richer uncertainty model.

## 3. Balanced execution

Four repetitions are frozen.

The four budget profiles are rotated so each occupies each execution position
exactly once.

Every profile observation is a fresh process.

Total physical observations:

`4 profiles x 4 repetitions = 16`.

## 4. Hard gates

Before budget interpretation:

- the governor must still select q={1,2,4,7} for the frozen breakpoints;
- every physical execution must be exact;
- every profile must produce the same output digest.

## 5. Compliance metric

For each observation:

```text
margin = declared_peak_budget - observed_normalized_peak
```

- margin >= 0 -> compliant
- margin < 0 -> calibration miss

The run records:

- observed peaks;
- compliance count;
- miss count;
- smallest margin;
- largest overrun;
- median work time.

## 6. Scientific interpretation

B471 distinguishes two very different claims:

1. **selection correctness relative to the old frontier**
2. **future budget compliance on a new run**

B470 already established (1).

B471 measures (2).

This is essential because:

```text
observed frontier != guaranteed future bound
```

A miss would therefore improve the governor by identifying uncertainty.

## 7. Claim ceiling

**HOSTED_OBSERVED_FRONTIER_GOVERNOR_CALIBRATION**

No worst-case memory guarantee is claimed.

## 8. Next

If boundary misses occur, B472 should derive explicit calibration headroom from
the new specimens and validate a margin-aware policy.

If no misses occur, B472 should still avoid claiming a worst-case guarantee and
expand independent repetitions before tightening the model.
