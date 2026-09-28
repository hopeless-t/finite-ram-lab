# CURRENT

> **Latest bounce:** B224
> **Stage:** STRATA-005 / REC-002 PASS / IMPLEMENT NEXT

## REC-002 canonical result

Hosted run:

`36427808785`

Result:

`SUCCESS / 16 of 16 valid trials`

All 8 paired blocks had recorder_on minus recorder_off MemoryHigh-event delta = 0.

Paired medians:

- max scan memory delta: -2,048 bytes
- scan elapsed delta: +724,882.5 ns
- scan elapsed ratio on/off: 1.0178166593

The timing data are runner-noisy and are not promoted to a universal overhead estimate.

Decision: use REC-001 in STRATA-005 at the tested recording density.

See `docs/REC-002-RESULT.md`.

## STRATA-005 frozen design

- MemoryHigh: 144 and 176 MiB
- arms: buffered, 48, 64, 80, 96 MiB
- 4 independent runner blocks per pressure setting
- 40 total new trials
- MemoryMax: 320 MiB
- hot anonymous memory: 64 MiB
- cold file: 96 MiB
- read chunk: 4 MiB

Primary question: does pressure-event onset track pressure headroom more consistently than a fixed release interval?

## Next action

Implement STRATA-005 runner, aggregation, tests, and hosted workflow.

Do not launch until implementation CI passes.

## Operating policy

Research is the mainline. Recorder failures discovered by real experiments are repaired atomically and promoted to regressions.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
