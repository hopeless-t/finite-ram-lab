# B472 — q=1 Targeted Tail Calibration v0.1

Status: **TARGETED FRESH-PROCESS TAIL PANEL**.

## 1. Why q=1 only

B471 produced 16 fresh governor-dogfood observations.

The observed-upper boundary succeeded for q=2, q=4, and q=7, but q=1 exceeded
its old empirical maximum in 2/4 runs.

Old B469 q=1 maximum:

`67,022,848 B`

B471 q=1 maximum:

`67,117,056 B`

The first calibration question is therefore narrow:

> Does the q=1 empirical maximum continue to move when we add a larger independent
> fresh-process panel under the same workload shape?

## 2. Frozen panel

Add:

`12`

new q=1 fresh-process observations.

Hold:

- size = 2048;
- lane_count = 7;
- tile_rows = 64;
- value_limit = 50;
- one deterministic seed;
- exact numerical semantics.

Prior comparable sample count:

`4 B469 + 4 B471 = 8`.

After B472:

`n = 20`.

## 3. Why sample count matters

For exchangeable future observations, the historical sample maximum has a simple
one-step rank bound.

With n comparable observations:

```text
P(next observation > historical maximum) <= 1/(n+1)
```

Therefore:

```text
P(next observation <= historical maximum) >= n/(n+1)
```

For n=20:

```text
20/21 ~= 95.238%
```

This is a distribution-free rank statement under the exchangeability assumption.

It is **not**:

- a worst-case memory guarantee;
- protection against runner drift;
- protection against a changed workload/runtime;
- a statement that the physical peak distribution is stationary forever.

## 4. Endpoints

B472 records:

- every new normalized peak;
- median new peak;
- new-panel maximum;
- number of new samples exceeding the prior union maximum;
- new union empirical maximum;
- total pooled sample count;
- rank-max one-step predictive coverage floor.

## 5. Classification

If no new sample exceeds 67,117,056 B:

`Q1_EMPIRICAL_MAX_STABLE_IN_TARGETED_PANEL`

Otherwise:

`Q1_EMPIRICAL_MAX_MOVED`

A moving maximum is not discarded as noise. It becomes the new empirical
boundary and evidence that more calibration is required.

## 6. Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_EMPIRICAL_MAX_CALIBRATION**

## 7. Next

If the q1 maximum is stable, B473 should expose the rank-based coverage metadata
to the governor and calculate the sample budget required for explicit target
coverage levels such as 95% and 99%.

If the maximum moves again, B473 should preserve the new specimen and avoid
promoting a 95%-style risk mode until enough comparable data are gathered.
