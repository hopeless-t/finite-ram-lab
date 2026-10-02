# B492 — Online Calibration Update v0.1

Status: **FAIL-CLOSED NON-DRIFT EVIDENCE ABSORPTION**.

## 1. Goal

B491 closed the first runtime loop:

```text
Governor decision
-> physical execution
-> boundary comparison
-> tail-vs-drift classification
```

B492 adds the next state transition:

```text
non-drift future panel
-> absorb evidence
-> update sample count / empirical maximum / coverage
```

## 2. Hard admission gates

The updater refuses the panel when:

- B491 reports any drift-suspect q;
- boundary dispatch checks failed;
- source schemas do not match the repaired-runtime calibration chain.

No threshold is silently widened after a drift alert.

## 3. Frozen B491 update

Previous B489 state:

- q2: n19, max 50,696,192 B
- q4: n19, max 58,941,440 B
- q7: n19, max 71,507,968 B

B491 contributes eight independent hosted-runner observations per q.

Therefore:

`n = 19 + 8 = 27`.

New rank-max one-step floor:

`27/28 ~= 96.429%`.

## 4. Empirical maximum update

q2 and q4 produced no new maxima, so their thresholds remain unchanged.

q7 produced one tail-compatible new maximum:

`71,512,064 B`

which is:

`+4,096 B`

above the previous calibration maximum.

The online state must preserve that page-level movement.

## 5. Why this is not "moving the goalposts"

The new q7 value is accepted only because:

1. it came from a predeclared runtime dogfood panel;
2. the panel passed exact semantics and boundary dispatch;
3. the exceedance count was not drift-suspect under the predeclared reference
   diagnostic.

A drift-suspect panel would reopen the probe/recalibration lane instead.

## 6. Updated evidence contract

After B492:

```text
q2: n27, max 50,696,192 B
q4: n27, max 58,941,440 B
q7: n27, max 71,512,064 B
```

All carry:

`27/28 ~= 96.429%`

sample-max one-step rank coverage under exchangeability.

## 7. Claim ceiling

**NON_DRIFT_ONLINE_SAMPLE_MAX_UPDATE**

This is an evidence-state transition, not a worst-case memory guarantee.

## 8. Next

B493 should compile the updated state into Governor v2.1 and verify that:

- q2/q4 breakpoints remain unchanged;
- q7 moves upward by exactly one page;
- the decision receipt exposes n=27 and coverage 27/28;
- a requested 99% coverage still fails closed.
