# CURRENT

> **Latest bounce:** B210
> **Stage:** REC-002 / IMPLEMENTED / ORDINARY CI PENDING

## REC-001

REC-001 v0 is repository-valid; parent CI run `36416819473` succeeded.

## REC-002

The frozen recorder-overhead screen is implemented.

Design:

- 8 hosted runner blocks;
- paired recorder_off / recorder_on;
- MemoryHigh = 160 MiB;
- MemoryMax = 320 MiB;
- STRATA DONTNEED 80 MiB boundary workload;
- 16 total trials;
- recorder_on emits 26 synchronous JSONL records;
- no SQLite ingestion in the measured interval.

Implementation launch is intentionally separate.

REC-002 runs only on manual dispatch or a commit touching `launch/REC-002-v1.txt`.

## Validation state

B210 ordinary CI has not yet been accepted.

## Next action

Read B210 CI exactly once.

- success -> add the explicit REC-002 launch marker in a new bounce;
- pending -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect failure only and do not launch.

STRATA-005 remains frozen and unlaunched.

## Authority boundary

Hosted research/repository work only.
No local-PC execution.
No STRATA-005 launch inferred.
No memory-control policy authorized.
