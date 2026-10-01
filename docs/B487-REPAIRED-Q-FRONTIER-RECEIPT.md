# B487 — Repaired q Frontier Receipt

Status: **PASS WITH HOLD / FRONTIER REBUILT, ALL-q REPAIR GATE NOT MET**

## Frozen execution

- workflow run: 36941540201
- aggregate job: 110634101889
- execution head: d6ddaba6caf54e28ad19e73081e8e9f88e8aa3a6
- tests: 4/4 PASS
- runner blocks: 8
- child observations: 64
- aggregate artifact ID: 11200620177
- artifact ZIP SHA256: 99f680a3375a8a3eeaec03116df105de6cf2dcae585de8232f18791a9ba0b481
- aggregate JSON SHA256: 6fe3498850d88de869b2dce5c6b8bd1b444b380dfecf4e88637766aef3b7f5af

## Paired old -> repaired peak effect

q1:
- old median peak = 67,084,288 B
- repaired = 50,667,520 B
- median saving = **16,416,768 B ~=15.66 MiB**
- peak saving 8/8 blocks, Holm significant
- repaired/old latency ratio ~=0.9871

q2:
- old median peak = 67,033,088 B
- repaired = 50,667,520 B
- saving = **16,365,568 B ~=15.61 MiB**
- 8/8, Holm significant
- latency ratio ~=0.9866

q4:
- old median peak = 71,268,352 B
- repaired = 58,925,056 B
- saving = **12,335,104 B ~=11.76 MiB**
- 8/8, Holm significant
- latency ratio ~=0.9919

q7:
- old median peak = 71,507,968 B
- repaired = 71,507,968 B
- median saving = **0 B**
- only one nonzero paired difference
- not significant
- latency ratio ~=0.9935

## Frozen integrated-repair gate

B487 preregistered:

- every q must show significant peak savings;
- minimum median saving across q >=12 MiB.

q7 does not satisfy that gate.

Therefore the declared classification remains:

**INTEGRATED_REPAIR_HOLD**

The gate is not relaxed after observation.

## New repaired q frontier

q1:
- median peak = 50,667,520 B
- median work = 0.405917 s

q2:
- median peak = 50,667,520 B
- median work = 0.397770 s
- **same median peak as q1**
- ~2.01% lower median latency than q1

q4:
- median peak = 58,925,056 B
- median work = 0.390193 s
- +8,257,536 B vs q1
- ~3.87% lower latency vs q1

q7:
- median peak = 71,507,968 B
- median work = 0.388038 s
- +20,840,448 B vs q1
- ~4.40% lower latency vs q1

Observed repaired Pareto set:

`{2,4,7}`

q1 is now strictly dominated by q2 on the median surface:

- same median peak;
- slower median work time.

This is a major topology change from the old B469 frontier, where all four q
values were Pareto.

## Interpretation of q7

B487 does not prove why q7 receives no peak benefit.

A strong candidate is peak bottleneck migration: when all seven residue lanes are
resident simultaneously, an earlier residency peak may already exceed the
centering temporary.

That mechanism needs stage evidence if it becomes decision-relevant.

For Governor purposes, the observed repaired q7 peak is sufficient; no q7
centering benefit is assumed.

## Calibration consequence

The repaired runtime is a different implementation and cannot inherit B475's
95%-coverage thresholds.

The B487 runner-block medians provide a new frontier prior only.

A new sample-max calibration must be collected for repaired q2/q4/q7.

q1 is not required for the production Pareto policy unless a later experiment
restores a unique constraint role.

## Claim ceiling

**HOSTED_PAIRED_OLD_VS_REPAIRED_Q_FRONTIER**

## Next

B488 should freeze the repaired Pareto surface and calculate/collect the
calibration budget needed for a 95%-class repaired Governor:

- q2
- q4
- q7

The old Governor v1 remains attached only to the BOOLEAN_INDEX implementation.
