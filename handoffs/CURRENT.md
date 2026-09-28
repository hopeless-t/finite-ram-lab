# CURRENT

> **Latest bounce:** B212
> **Stage:** REC-002 / HOSTED LAUNCH REQUESTED

## B210 implementation acceptance

Commit:

`175d7a9232ead6f3ce39a5c0e57d7583d38ff1e0`

Ordinary CI run `36417680847` completed successfully.

## REC-002 launch

The explicit launch marker now exists:

`launch/REC-002-v1.txt`

This is the only newly authorized hosted execution.

Frozen design:

- 8 hosted runner blocks;
- paired recorder_off / recorder_on;
- 16 total trials;
- MemoryHigh=160 MiB;
- MemoryMax=320 MiB;
- hot anonymous memory=64 MiB;
- cold file=96 MiB;
- DONTNEED=80 MiB;
- recorder_on emits 26 synchronous JSONL records;
- no SQLite ingest in the measured interval.

## Next action

Read the REC-002 workflow for the B212 launch commit exactly once.

- success -> inspect aggregate artifact once and canonicalize the observer-effect result;
- pending -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect failure only; no blind retry.

## Parent research state

REC-001 v0 is repository-valid.

STRATA-005 remains frozen from B206 and unlaunched.

## Authority boundary

Hosted REC-002 only.
No local-PC execution.
No STRATA-005 launch inferred.
No memory-control policy authorized.
