# CURRENT

> **Latest bounce:** B230
> **Stage:** STRATA-005 / HOSTED RUN LAUNCHED + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## REC-002

Canonical hosted PASS:

- run: `36427808785`
- trials: 16 / 16
- all 8 paired blocks: recorder-induced MemoryHigh-event delta = 0
- Recorder accepted for STRATA-005 at the tested 26-record density

## STRATA-005 frozen contract

- MemoryHigh: 144 / 176 MiB
- arms: buffered / DONTNEED 48 / 64 / 80 / 96 MiB
- 4 blocks per pressure
- 40 total trials
- 26 REC-001 records per trial
- aggregate reports raw-MiB and release/high onset screens

Pre-launch ordinary CI `36428893054`: completed / success.

## Launch

Exact launch commit:

`93283b041c53db57dab709f7f433e464037358c9`

Explicit marker:

`launch/STRATA-005-v1.txt`

Hosted STRATA-005 run:

`36430416271`

Single discovery/status read in B230:

`queued`

Do not poll again in this bounce.

Ordinary CI `36430416229` was also created by the launch commit; it is not the scientific result and was not polled.

## Source intake

`docs/NAIVE-N05-FLASH-INTAKE-v1.md` records the Naive-N0.5-Flash intake.

Council result remains:

- DONTNEED evidence transfer: NO
- mechanism transfer: YES
- measurement-design transfer: STRONG YES
- semantic reuse distance: future-study proposal only

## Next fresh-bounce action

Read run `36430416271` exactly once.

- success -> fetch artifacts once and validate/atomize all 40 trials;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant; no blind rerun.

After valid cross-pressure observations exist, revisit whether Monte Carlo adds information.

## Operating policy

Research remains mainline.
Recorder repair remains sidecar work driven by concrete counterexamples.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
