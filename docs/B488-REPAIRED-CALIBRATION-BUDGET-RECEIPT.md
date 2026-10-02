# B488 — Repaired Frontier Calibration Budget Receipt

Status: **PASS / 33-RUNNER OBSERVATION BUDGET FROZEN**

## Frozen execution

- workflow run: 36952667022
- job: 110668780517
- execution head: a385de584342323f6bf8c0bd25a38214372c154a
- tests: 4/4 PASS
- artifact ID: 11203783867
- artifact ZIP SHA256: d3776a39ce4d1c8c3cde2337d4d750c2998000caee6f523b84e3abc31e91900f
- budget SHA256: 33de390920e924fc4b0ea8edcfb695425c0009a5a8d23bcd232770b4fabebefd

## Repaired Pareto policy surface

Production calibration candidates:

- q2
- q4
- q7

q1 is excluded because B487 observed q2 at the same median peak and lower median latency.

## Existing evidence

B487 provides eight independent hosted-runner observations per Pareto q.

Thus:

`n=8`

and the exchangeability-conditional sample-max one-step rank floor is:

`8/9 ~= 88.889%`.

## Frozen 95% budget

95% requires:

`n>=19`.

Therefore:

- q2: +11 runner observations
- q4: +11
- q7: +11

Total:

`33 independent runner observations`.

## Scientific unit

The primary calibration unit is the hosted-runner job, not child-process
repetition within one VM.

This preserves the runner-level variation exposed by B479-B487.

## Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_REPAIRED_CALIBRATION_BUDGET**

## Next

B489 must spend exactly the frozen 33-observation budget using the repaired
TILED_WHERE runtime and update the pooled empirical maxima for q2/q4/q7.

No old BOOLEAN_INDEX threshold may enter the repaired calibration.
