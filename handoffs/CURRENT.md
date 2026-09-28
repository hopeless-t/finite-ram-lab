# CURRENT

> **Latest bounce:** B223
> **Stage:** RESEARCH MAINLINE / REC-002 RELAUNCH + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Operating policy

Recorder is treated as research-ready / fail-visible for the current scope.

Research experiments are the mainline again. Recorder hardening continues only when real runs expose defects or a meaningful Recorder change warrants bounded robustness validation.

REC-003 100k Monte Carlo remains available but is not a prerequisite for research progress.

## REC-002

Relaunch commit:

`15530bfa7e619e44e97302109422f7331d131dc5`

Hosted REC-002 run:

`36427808785`

Last and only status read in B223:

`queued`

Do not poll again in the same bounce.

## Next fresh-bounce action

Read REC-002 run `36427808785` once.

- success -> inspect aggregate observer-effect evidence;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> inspect and repair only the exposed failure.

If REC-002 supports Recorder use under the boundary workload, move directly back to STRATA-005 external-validity work.

## STRATA-005

Frozen design remains:

- MemoryHigh 144 and 176 MiB;
- five-arm panel: buffered, 48, 64, 80, 96 MiB;
- four runner blocks per setting;
- 40 new trials;
- normalized headroom analysis.

No launch yet.

## Authority boundary

Hosted research only.
No local-PC execution.
No STRATA-005 launch inferred from this checkpoint.
No memory-control policy authorized.
