# CURRENT

> **Latest bounce:** B251
> **Stage:** STRATA-008 / EXPLICIT HOSTED LAUNCH
> **Turn stop reason:** RUN_DISCOVERY_PENDING

## Validation

Implementation commit:

`d709e9e7c71b03faa9e519079c42663f3feb3a8e`

CI:

`36436853395`

Single B251 read:

- completed
- success

## Launch

B251 creates:

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

96 MiB STRATA-007 remains historical anchor only.

## Next fresh-bounce action

Discover/read the STRATA-008 workflow run for the exact B251 launch commit once.

- success -> fetch aggregate artifact once and validate/atomize 24 trials;
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
