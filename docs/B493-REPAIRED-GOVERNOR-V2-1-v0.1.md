# B493 — Repaired Governor v2.1 v0.1

Status: **ONLINE-EVIDENCE-UPDATED SOFTWARE GOVERNOR**.

## 1. Source state

B493 compiles:

- B490 latency ordering / repaired Pareto policy structure;
- B492 updated online evidence state.

No old BOOLEAN_INDEX evidence is imported.

## 2. Updated breakpoints

### q2

- peak breakpoint = 50,696,192 B
- n = 27
- rank-max floor = 27/28 ~=96.4286%

### q4

- peak breakpoint = 58,941,440 B
- n = 27
- rank-max floor ~=96.4286%

### q7

- previous v2 breakpoint = 71,507,968 B
- v2.1 breakpoint = **71,512,064 B**
- movement = +4,096 B
- n = 27
- rank-max floor ~=96.4286%

## 3. Runtime consequence

At exactly the old q7 boundary:

`71,507,968 B`

Governor v2.1 must no longer choose q7.

It falls back to q4 because the absorbed B491 evidence moved the q7 empirical
maximum by one page.

At:

`71,512,064 B`

q7 becomes eligible again.

This is the concrete behavior expected from evidence-preserving online learning.

## 4. Coverage

All three q values now carry:

`27/28 ~= 0.9642857`

one-step sample-max rank coverage under exchangeability.

A 99% request still fails closed because n=27 is below the required n=99.

## 5. Latency source

B493 reuses the repaired-runtime latency ordering frozen by B490.

B492 changed the evidence boundary/count state, not the execution strategy.

A later latency-drift lane can refresh this component independently.

## 6. Claim ceiling

**NON_DRIFT_UPDATED_REPAIRED_GOVERNOR_V2_1**

## 7. Milestone

The full loop is now executable:

```text
research mechanism
-> implementation repair
-> repaired frontier
-> 95% calibration
-> Governor v2
-> runtime dogfood
-> tail/drift diagnosis
-> fail-closed evidence absorption
-> Governor v2.1
```

## 8. Next

The next application-oriented step is to expose this policy as a stable GitHub
Actions command/artifact surface so ordinary jobs can ask:

```text
given RAM budget + required coverage -> selected q + evidence receipt
```

without importing the research harness directly.
