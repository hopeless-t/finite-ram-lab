# B476 — Tail Risk vs Drift Diagnostic v0.1

Status: **COVERAGE-AWARE GOVERNOR DOGFOOD / BATCH DIAGNOSTIC**.

## 1. Question

B475 can make a q decision with an explicit sample-max rank coverage contract.

A future execution may still exceed the calibrated empirical maximum.

The next problem is:

> Is a new maximum merely compatible with the declared tail risk, or is the
> exceedance pattern strong enough to suspect that the calibration population
> no longer matches current execution?

B476 introduces the first bounded diagnostic for that distinction.

## 2. Frozen calibration points

The v1 governor calibration entering B476 is:

- q1: boundary 67,117,056 B, n=20, one-step rank floor ~=95.238%
- q2: boundary 67,194,880 B, n=19, floor=95%
- q4: boundary 71,389,184 B, n=19, floor=95%
- q7: boundary 71,544,832 B, n=19, floor=95%

B476 verifies that these boundary budgets still select q1/q2/q4/q7 respectively
under Governor v1 before physical execution.

## 3. New physical panel

For each q:

- 8 new fresh-process observations;
- exact numerical workload;
- fixed size 2048;
- fixed lane count 7;
- fixed tile_rows 64;
- fixed value range;
- fixed seed for the workload shape.

Total:

`32 fresh-process observations`.

The four q values are balanced across execution positions by repeating the
qualified four-order schedule twice.

## 4. Why one exceedance is not drift

A 95%-class sample-max contract explicitly permits future new maxima.

Therefore:

```text
new maximum
!=
automatic drift
```

B476 counts strict exceedances of the frozen calibration maximum in the future
8-run batch for each q.

## 5. Batch reference model

For the batch diagnostic only, B476 adds a stronger explicit reference model:

- future observations are comparable to calibration observations;
- an IID continuous reference is used for the exceedance-count calculation.

Under an IID continuous distribution, if the calibration sample maximum came from
n observations, then the unknown strict-tail mass beyond that maximum has the
distribution:

`Beta(1,n)`.

For m future observations, the count K of values exceeding the frozen calibration
maximum therefore follows a Beta-Binomial predictive distribution:

`K ~ BetaBinomial(m, alpha=1, beta=n)`.

This handles the uncertainty of the calibrated maximum itself instead of treating
the nominal 5% ceiling as a known fixed Bernoulli probability.

## 6. Familywise drift-suspect rule

B476 uses:

- family alpha = 0.05
- four q tests
- Bonferroni per-q alpha = 0.0125

With m=8 future observations and n=19 or n=20 calibration samples:

- 1 exceedance is compatible with the ordinary tail;
- 2 exceedances remain compatible;
- 3 exceedances remain above the familywise threshold;
- **4 or more exceedances in 8** cross the current drift-suspect threshold.

This is a diagnostic threshold, not proof of drift.

## 7. Classifications

Per q:

- `NO_NEW_MAX`
- `TAIL_COMPATIBLE_EXCEEDANCE`
- `LOCAL_DRIFT_SUSPECT`

Overall:

- `NO_BOUNDARY_EXCEEDANCES`
- `TAIL_COMPATIBLE_EXCEEDANCES`
- `DRIFT_SUSPECT`

A non-significant batch does not prove the absence of drift.

## 8. Discrete-memory caveat

VmHWM is page-quantized and ties are common.

The exact Beta-Binomial derivation assumes a continuous IID reference.

Therefore the calculation is kept under the claim ceiling:

**IID_CONTINUOUS_REFERENCE_TAIL_VS_DRIFT_DIAGNOSTIC**

The result should be treated as a bounded reference diagnostic, not a final drift
detector.

## 9. Why this matters for the application

The runtime can now distinguish these actions:

```text
isolated / tail-compatible exceedance
  -> record specimen
  -> keep current model provisionally

clustered exceedances inconsistent with reference tail
  -> DRIFT_SUSPECT
  -> stop treating old coverage as current
  -> reopen OBSERVE / PROBE / recalibration
```

That is the first step toward a governor that manages the validity of its own
evidence model.

## 10. Next

If B476 sees only tail-compatible behavior, B477 should add a second drift signal
based on location/level shift rather than maxima alone.

If B476 flags a q, B477 should perform a targeted condition biopsy before
recalibrating the whole frontier.
