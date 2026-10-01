# B476 — Tail Risk vs Drift Receipt

Status: **PASS / EXCEEDANCES TAIL-COMPATIBLE**

## Frozen execution

- workflow run: 36935922386
- job: 110616052777
- execution head: 073ca34765c893998d86f9914f8df9d62835bce2
- tests: 4/4 PASS
- artifact ID: 11198247150
- artifact ZIP SHA256: 09c3a3550b7aaf0adf7fb48f1e7fe846cfd899d513f0a40d52fb1efc318aaa3b
- panel SHA256: 1675a7ecacbdcef3af9421df7e34ba1ebc519cc3e699b6c75249b1b72756e8df

## Future panel

Eight fresh-process observations per q.

Total:

`32`

Every observation preserved exact numerical semantics.

## q1

- calibration max: 67,117,056 B
- calibration n: 20
- new maximum exceedances: 0/8
- new-panel maximum: 67,059,712 B
- classification: NO_NEW_MAX

## q2

- calibration max: 67,194,880 B
- calibration n: 19
- new maximum exceedances: 0/8
- new-panel maximum: 67,059,712 B
- classification: NO_NEW_MAX

## q4

- calibration max: 71,389,184 B
- calibration n: 19
- new maximum exceedances: 0/8
- new-panel maximum: 71,262,208 B
- classification: NO_NEW_MAX

## q7

- calibration max: 71,544,832 B
- calibration n: 19
- new maximum exceedances: 2/8
- strict new maxima:
  - 71,561,216 B
  - 71,610,368 B
- largest overrun: 65,536 B

Under the IID-continuous Beta-Binomial reference:

`P(K >= 2 | n=19,m=8) ~= 0.07977`.

Four-q Bonferroni threshold:

`0.05/4 = 0.0125`.

Therefore q7 is classified:

**TAIL_COMPATIBLE_EXCEEDANCE**

not drift suspect.

## Overall

Classification:

**TAIL_COMPATIBLE_EXCEEDANCES**

Suspect q:

`[]`

## Scientific interpretation

A new maximum occurred, but the batch pattern is still compatible with the
declared tail uncertainty of the calibrated sample maximum.

This is the first concrete demonstration of the intended distinction:

```text
new maximum
!=
automatic drift
```

The governor should record the q7 specimens without immediately discarding the
calibration model.

## Important caveat

The batch diagnostic uses an IID continuous reference model.

VmHWM is discrete/page-quantized and ties are common.

The result is therefore a bounded diagnostic, not proof that no drift exists.

## Next

B477 should add a second drift signal based on level/location shift rather than
new maxima.

A distribution may move upward while still producing few or no strict new
maxima, especially with short batches and quantized measurements.
