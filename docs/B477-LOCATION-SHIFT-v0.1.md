# B477 — Exact Location-Shift Diagnostic v0.1

Status: **OFFLINE EXACT-PERMUTATION DRIFT SIGNAL**.

## 1. Why a second signal is needed

B476 saw two q7 strict new maxima but the exceedance count remained compatible
with the calibrated tail reference.

A distribution can also drift without creating many new maxima.

B477 therefore compares the recent calibration batch and the B476 future batch
using an exact rank-based location test.

## 2. Frozen batch sources

q1 reference:

- B472 12-run targeted q1 panel
- seed 472

q2/q4/q7 reference:

- B474 11-run calibration expansion
- seed 474

Future:

- B476 8-run per-q panel
- seed 476

The exact raw peak arrays are frozen in:

`analysis/inputs/B477-LOCATION-SHIFT-INPUT-v0.1.json`.

## 3. Statistic

For each q:

1. pool reference and future peak values;
2. assign midranks, preserving ties;
3. compute the future-group rank sum;
4. enumerate every labeling with the same future-group size;
5. compute an exact two-sided permutation p-value.

This requires no continuous-value approximation and handles page-quantized ties
directly.

## 4. Familywise threshold

Four q values are tested.

- family alpha = 0.05
- Bonferroni per-q alpha = 0.0125

A q is labeled location-shift suspect only when the exact permutation p-value is
at or below 0.0125.

Direction is reported from the median delta:

- LOCATION_SHIFT_UP_SUSPECT
- LOCATION_SHIFT_DOWN_SUSPECT
- LOCATION_SHAPE_SHIFT_SUSPECT

## 5. Critical confound

The historical and future batches use different deterministic input seeds.

Therefore a significant difference cannot yet be attributed uniquely to:

- runner/time/environment drift;
- workload-seed effect;
- interaction between the two.

B477 intentionally uses the claim ceiling:

**SEED_CONFOUNDED_EXACT_PERMUTATION_LOCATION_DIAGNOSTIC**

## 6. Why this is still useful

A significant location difference says:

> The B476 batch is not behaving like the recent calibration batch under a simple
> exchangeability interpretation.

It does not yet say why.

That is enough to justify a controlled replay experiment.

## 7. Next

If B477 flags q values, B478 should replay both the historical calibration seed
and the B476 seed in the same current runner environment, with fresh-process
order balancing.

Interpretation:

- seed effect persists within current environment -> workload-seed contribution;
- both seeds move together away from historical level -> temporal/runner drift;
- interaction -> keep both factors and expand the design.
