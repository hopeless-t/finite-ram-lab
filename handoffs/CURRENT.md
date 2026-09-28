# CURRENT

> **Latest bounce:** B214
> **Stage:** REC-002 / INFRASTRUCTURE FAILURE FIXED / CI PENDING

## REC-002 run 1

Hosted run `36419229167` = `completed / failure`.

All 8 blocks failed before measurement because the generated CSV schedule used CRLF and Bash retained `\\r` in the final `mode` field. Representative error:

`argument --mode: invalid choice: 'recorder_off\\r'`

There are zero valid observer-effect trials from this run. It must not be interpreted as recorder or pressure evidence.

## B214 fix

The schedule producer now explicitly uses LF-only CSV via `lineterminator="\\n"` and a byte-level regression test rejects carriage returns.

This is a portability/interface correction. It does not authorize an automatic rerun.

## Next fresh-bounce action

Read ordinary CI for the B214 fix exactly once.

- success -> accept the fix and create a distinct REC-002 relaunch marker/commit;
- pending -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect failure only; no blind retry.

## Parent research state

REC-001 v0 remains repository-valid.

STRATA-005 external-validity design remains frozen from B206 and unlaunched.

## Authority boundary

Hosted research/repository work only.
No local-PC execution.
No STRATA-005 launch inferred.
No memory-control policy authorized.
