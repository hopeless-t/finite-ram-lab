# CURRENT

> **Latest bounce:** B227
> **Stage:** STRATA-005 / RECORDER PATH REPAIRED + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## REC-002

Canonical hosted PASS:

- run: `36427808785`
- trials: 16 / 16
- all 8 paired blocks: recorder-induced MemoryHigh-event delta = 0
- Recorder accepted for STRATA-005 at the tested 26-record density

## STRATA-005

B226 commit:

`645c119257c53243bfa444962f96d4ea368ab9cb`

Execution contract now matches the frozen design and Recorder policy.

Each of the future 40 trials will:

- execute under MemoryHigh 144 or 176 MiB;
- use one of buffered / 48 / 64 / 80 / 96 MiB arms;
- emit exactly 26 REC-001 raw records;
- emit one trial JSON with raw and normalized outcomes.

The aggregate validates the exact 2 x 4 x 5 matrix and reports raw-MiB and release/high onset screens.

## Hosted validation

Ordinary CI:

`36428893054`

Last and only status read in B227:

`in_progress`

Do not poll again in the same bounce.

## Next fresh-bounce action

Read `36428893054` once.

- success -> explicit STRATA-005 launch marker and 40-trial hosted run;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> repair the exposed invariant only.

## Operating policy

Research remains mainline. Recorder repair is sidecar work driven by concrete counterexamples.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
