# B489 — Repaired Runtime 95% Calibration Receipt

Status: **PASS / ALL REPAIRED PARETO q AT 95%-CLASS COVERAGE**

## Frozen execution

- workflow run: 36952934068
- aggregate job: 110669736366
- execution head: 294aecd68b3d5c6fc662d50bffb915b70189d0e3
- tests: 4/4 PASS
- new runner blocks: 11
- new physical observations: 33
- aggregate artifact ID: 11204389942
- artifact ZIP SHA256: 6271694f819f7cc2a2777c8cc702482fc63ef216f2fa18eaaad14974816446ad
- calibration JSON SHA256: 9c78c95f69be26de60ef22332c03fa9261d7fc30e204382d53781935aff36e09

## q2

B487 raw samples:

`n=8`

B489 new samples:

`n=11`

Pooled:

`n=19`

Pooled empirical max:

`50,696,192 B`

New-panel maximum:

`50,688,000 B`

New observations above old maximum:

`0/11`

Rank-max one-step coverage floor:

`19/20 = 95%`

## q4

Pooled empirical max:

`58,941,440 B`

New-panel maximum:

`58,925,056 B`

New observations above old maximum:

`0/11`

Pooled n:

`19`

Coverage floor:

`95%`

## q7

Pooled empirical max:

`71,507,968 B`

New-panel maximum:

`71,507,968 B`

New observations above old maximum:

`0/11`

Pooled n:

`19`

Coverage floor:

`95%`

## Combined result

All repaired Pareto q values now meet the frozen 95%-class sample-count target.

Unlike the earlier BOOLEAN_INDEX calibration expansion, none of the new B489
runner observations moved the repaired empirical maxima.

This does not prove the maxima are hard bounds; it says the 19-sample repaired
calibration is internally stable over this added runner panel.

## Claim ceiling

**EXCHANGEABILITY_CONDITIONAL_REPAIRED_95P_CALIBRATION**

## Next

B490 should construct Coverage-Aware Governor v2 using only repaired-runtime
evidence:

- q2: max 50,696,192 B, n19, 95%
- q4: max 58,941,440 B, n19, 95%
- q7: max 71,507,968 B, n19, 95%

q1 remains excluded because B487 found it dominated by q2 on the repaired median
surface.

The old B475 Governor remains attached only to BOOLEAN_INDEX.
