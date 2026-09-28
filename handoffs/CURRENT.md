# CURRENT

> **Latest bounce:** B252
> **Stage:** STRATA-008 / LAUNCH COMMITTED + RUN MATERIALIZATION WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Leading mechanism

Current hosted evidence supports:

`K ~= MemoryHigh - effective_live_set`

across pressure, hot live-set, and Ubuntu image changes.

## STRATA-008 launch

Exact B251 launch commit:

`1843e566c8cf6e18322861cd6c7ee51b28cccc30`

Explicit marker:

`launch/STRATA-008-v1.txt`

Frozen execution:

- Ubuntu 26.04
- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 192 MiB
- read chunk 4 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 trials
- REC-001 50 records/trial

96 MiB cold-file STRATA-007 remains historical anchor only.

## Run discovery

One exact-head discovery read after B251 returned:

`0 matching workflow runs`

Do not infer failure and do not launch again.

## Next fresh-bounce action

Search exact head `1843e566c8cf6e18322861cd6c7ee51b28cccc30` for push-triggered runs once.

- STRATA-008 success -> fetch aggregate artifact once and validate/atomize 24 trials;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant;
- absent -> EXTERNAL_WAIT without retry.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
No blind retry after unknown delivery.
