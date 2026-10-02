# B491 — Repaired Governor v2 Boundary Dogfood Receipt

Status: **PASS / ONE TAIL-COMPATIBLE q7 EXCEEDANCE**

## Frozen execution

- workflow run: 36953403574
- aggregate job: 110671162927
- execution head: d07095d1b655138826ec95b59dfa185996a99f48
- tests: 4/4 PASS
- runner blocks: 8
- physical observations: 24
- artifact ID: 11204269349
- artifact ZIP SHA256: 46e4ce86abb9f1ab8cfdcdefc3570b83391ce689eb86933a2f37ecbf90efcee5
- result SHA256: 9cfa432e5acb566fd61e8ddb7d91b9877426ccbe56a8c468a06c5a16f197b560

## Boundary dispatch

All software transition checks passed:

- q2 boundary - 1 -> no eligible q
- q2 boundary -> q2
- q4 boundary - 1 -> q2
- q4 boundary -> q4
- q7 boundary - 1 -> q4
- q7 boundary -> q7

## q2

Declared boundary:

`50,696,192 B`

Future panel:

- 0/8 exceedances
- maximum = 50,667,520 B

Classification:

**NO_EXCEEDANCE**

## q4

Declared boundary:

`58,941,440 B`

Future panel:

- 0/8 exceedances
- maximum = 58,925,056 B

Classification:

**NO_EXCEEDANCE**

## q7

Declared boundary:

`71,507,968 B`

Future panel:

- 1/8 exceedance
- new maximum = 71,512,064 B
- overrun = **4,096 B = one page**

Under the Beta-Binomial future-batch reference with n=19,m=8:

`P(K>=1) ~= 0.2963`

Per-q drift threshold:

`0.05/3 ~= 0.01667`

Classification:

**TAIL_COMPATIBLE_EXCEEDANCE**

not drift suspect.

## Overall

**TAIL_COMPATIBLE_EXCEEDANCES**

Suspect q:

`[]`

This is the expected behavior of a probabilistic empirical-max contract:

```text
new maximum
!=
automatic drift
```

## Next

B492 should implement the first online calibration update rule.

Because the new panel is not drift-suspect:

- append all 8 new observations per q to the calibration population;
- update n from 19 to 27;
- update the q7 empirical maximum by +4 KiB;
- recompute the rank-max one-step floor as 27/28 ~=96.429%;
- preserve q2/q4 maxima if unchanged.

If a future panel is drift-suspect, the same updater must fail closed instead of
absorbing the observations automatically.
