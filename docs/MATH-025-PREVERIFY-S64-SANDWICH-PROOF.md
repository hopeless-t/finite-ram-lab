# MATH-025 — PREVERIFY_S64 sandwich proof and premeasurement-history signal

## Frozen observations

B405 R8 trial `0:0` produced:

- 64 complete NORMALIZE touches;
- all measured touches on stock CPU 3;
- worker touch sequence 1..64 without error;
- zero measured VmPTE growth;
- zero trace gaps;
- zero target-worker direct Q64 events in those 64 measured windows;
- zero missed hits on the critical `frl_pc_try64` probe in the block.

R9 / `TX-NORMALIZE-BOUNDARY-CHASE-v1` then measured 32 new fresh identities with target-PID + stock-CPU Q64 attribution.

R9 result:

```text
32/32 valid
32/32 WITHIN_BOUND
bound violations = 0
critical Q64 probe coverage = PASS
max observed T = 48
```

First-Q64 histogram:

```text
T=1   26
T=2    2
T=27   1
T=46   2
T=48   1
```

## Sandwich proof for R8

Let `S0` be the usable target stock immediately before the first measured R8 NORMALIZE touch.

From MATH-024 / Linux source semantics:

```text
S0 <= 64.
```

R8 performed 64 clean one-page measured faults without a target direct-Q64 event.

Under the frozen one-page consumption assumptions, each such touch can consume at most one stock credit before a direct charge becomes necessary.

Therefore:

```text
S0 >= 64.
```

Combining the independent bounds:

```text
S0 <= 64
S0 >= 64
---------
S0 = 64.
```

This names the R8 state:

```text
PREVERIFY_S64
```

and its observed boundary phenotype:

```text
MAX_STOCK_BOUNDARY
```

The protocol stopped after touch 64, so touch 65 was not physically executed in R8.

The theorem predicts the next direct-charge boundary at:

```text
T = S0 + 1 = 65.
```

This is a deduction from the source upper bound plus the frozen R8 lower bound. It is not a retroactive observed touch-65 receipt.

## R9 supports the source bound

R9 deliberately extended the primary horizon to touch 65 and the diagnostic horizon to touch 80.

No identity crossed the primary bound:

```text
max T = 48
T > 65 = 0/32
no-Q64-through-80 = 0/32.
```

So R9 found no counterexample to the one-slot stock bound.

R9 did not re-capture `T=65`; therefore it does not estimate how often PREVERIFY_S64 occurs.

## Initial residuals inferred from R9

For clean within-bound identities:

```text
S0 = T - 1.
```

Observed inferred residuals were:

```text
S0=0   26
S0=1    2
S0=26   1
S0=45   2
S0=47   1
```

This confirms that pre-VERIFY initial state is not a single reset value.

## Premeasurement target-Q64 history

R9 also recorded target-PID Q64 events on the stock CPU before measured touch 1.

Grouped result:

```text
pre-Q64 count 0 -> T = 1 x26, T = 2 x2
pre-Q64 count 6 -> T = 27 x1
pre-Q64 count 7 -> T = 46 x2, T = 48 x1
```

All 32 cgroups contained exactly one process: the target worker PID.

The design-internal association is strong:

```text
Pearson r ~= 0.988
Spearman rho ~= 0.843
```

These correlations are descriptive only.

They do not prove that Q64 count alone determines residual stock, because the premeasurement interval does not yet record refill sizes, successful stock consumption, or drain call paths.

## Updated model

The Chapter-II state model now separates:

```text
NATURAL PRE-VERIFY STATE
    history-dependent S0 in [0,64]

MEASURED DIRECT-Q64 PRIMER
    deterministic verified reset R0=63
```

This removes the apparent conflict between R8's 64-touch normalization exhaustion and the established verified `R0=63` arithmetic.

## Next falsifiable question

The highest-value next question is now:

> What kernel allocation/refill sequence during the migration-to-first-touch interval constructs the high pre-VERIFY stock states?

A dedicated premeasurement call-path experiment should observe, for the target PID on the stock CPU:

- direct Q64 charge call paths;
- refill sizes;
- drain events;
- migration-to-first-touch timing;
- resulting first measured Q64 boundary T.

The goal is to replace the correlation:

```text
premeasurement Q64 burst -> high S0
```

with a source-grounded causal ledger.

## Claim ceiling

PREVERIFY_S64 is established for the frozen R8 specimen under the explicit one-page and observer-completeness assumptions.

R9 validates the <=65 bound in 32 additional identities but does not estimate the population frequency of PREVERIFY_S64.
