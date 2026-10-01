# B478 — Seed vs Temporal Replay Receipt

Status: **PASS / q4 SEED EFFECT, q2 MIXED EFFECT**

## Frozen execution

- workflow run: 36936705161
- job: 110618539217
- execution head: a97e8525ce018317bbbdac2e183a19af6d2522b9
- tests: 3/3 PASS
- artifact ID: 11197788009
- artifact ZIP SHA256: 692ec4b51194485d4c8a9bb5b479b5f6f32f24ac3757d87c97c2c106bb53eaee
- result SHA256: d523bdd73da4bb0ad15535278fba28fc93fcfb4018575bd1b049d72b93930f3b

## q2

Historical seed474 median:

`67,100,672 B`

Current seed474 median:

`67,129,344 B`

Current seed476 median:

`66,973,696 B`

Temporal/runner comparison:

- delta = +28,672 B
- exact p ~= 0.006298

Seed comparison inside current environment:

- seed476 - seed474 = -155,648 B
- exact p ~= 0.0001554

Classification:

**MIXED_TEMPORAL_AND_SEED_SHIFT_SUSPECT**

## q4

Historical seed474 median:

`71,303,168 B`

Current seed474 median:

`71,313,408 B`

Current seed476 median:

`71,198,720 B`

Temporal/runner comparison:

- delta = +10,240 B
- exact p ~= 0.44914

Seed comparison inside current environment:

- seed476 - seed474 = -114,688 B
- exact p ~= 0.0001554

Classification:

**WORKLOAD_SEED_EFFECT_SUSPECT**

## Interpretation

The B477 q4 downward location shift is strongly consistent with a workload-seed
effect in this replay.

q2 is different:

- a strong seed effect exists;
- a smaller but familywise-significant historical-vs-current seed474 shift also
  remains.

Therefore q2 cannot yet be treated as seed-only.

## Why this matters for the Governor

A single q peak distribution cannot safely ignore workload identity.

At least for q2/q4, the workload seed changed the measured process-peak location
by around 0.11-0.16 MiB in this experiment.

That is small compared with the multi-MiB q frontier but large relative to the
tens-of-KiB confidence/boundary refinements being used by the governor.

## Next

B479 should treat each GitHub-hosted runner job as an independent block.

Replay q2/q4 and both seeds across multiple runner instances.

Questions:

1. Is the seed effect repeatable across runner blocks?
2. Is q2 seed474 persistently shifted from the historical level, or was B478 one
   runner-instance offset?
3. How large is between-runner block variance relative to within-runner process
   variance?
