# B477 — Exact Location-Shift Receipt

Status: **PASS / q2,q4 LOCATION SHIFT SUSPECT**

## Frozen execution

- workflow run: 36936439619
- job: 110617697326
- execution head: fb8e4b42d31fb246db6e7fa44a3f05a0901aa74f
- tests: 4/4 PASS
- artifact ID: 11197777515
- artifact ZIP SHA256: 0cb448a8bcb859d605fdfbdea1febed4a89958b3c9a50d6d80696ca71b31d051
- result SHA256: 32aceab8fb0a0bc174045c06919b715715effb34a5b23218600fd3a59cf64f0c

## Exact permutation results

q1:
- reference median = 66,994,176 B
- B476 median = 66,983,936 B
- delta = -10,240 B
- exact p = 0.805811
- LOCATION_COMPATIBLE

q2:
- reference median = 67,100,672 B
- B476 median = 66,973,696 B
- delta = -126,976 B
- exact p ~= 3.969e-5
- LOCATION_SHIFT_DOWN_SUSPECT

q4:
- reference median = 71,303,168 B
- B476 median = 71,168,000 B
- delta = -135,168 B
- exact p ~= 1.985e-4
- LOCATION_SHIFT_DOWN_SUSPECT

q7:
- reference median = 71,507,968 B
- B476 median = 71,507,968 B
- delta = 0
- exact p = 0.334021
- LOCATION_COMPATIBLE

Per-q familywise threshold:

`0.0125`

## Combined interpretation with B476

B476:
- q7 produced two new maxima;
- exceedance batch was tail-compatible.

B477:
- q7 shows no location shift;
- q2/q4 show strong downward location shifts without new maxima.

Therefore the two diagnostics are detecting different structure:

```text
tail/extreme behavior != distribution location behavior
```

## Confound

The q2/q4 historical reference batch used deterministic seed 474.

B476 used seed 476.

The observed location shift therefore cannot yet be uniquely attributed to
temporal/runner drift.

## Next

B478 should replay seed474 and seed476 in the same current hosted environment for
q2 and q4.

For each q, compare:

1. current seed474 vs current seed476;
2. historical seed474 vs current seed474.

This can separate workload-seed contribution from temporal/runner contribution.
