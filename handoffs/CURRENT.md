# CURRENT

> **Latest bounce:** B256
> **Stage:** STRATA-009 IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Parent mechanism

STRATA-008 showed that doubling one-shot cold capacity from 96 to 192 MiB did not move the `80 < K <= 88 MiB` knee.

Empirical bootstrap found only bounded sub-MiB non-hot-floor movement.

## STRATA-009 implementation

Exact B255 commit:

`fe819f2fa9948c6fa63e741919f997e25f7daffa`

Frozen boundary test:

- Ubuntu 26.04
- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 384 MiB
- read chunk 4 MiB
- DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- buffered intentionally omitted
- 4 blocks
- 20 trials
- REC-001 98 records/trial

384 MiB dataset capacity is larger than MemoryMax=320 MiB.

Question:

Can bounded DONTNEED streaming preserve the same instantaneous-memory knee even when total dataset capacity exceeds the cgroup memory cap?

No launch marker exists.

## CI

Exact-head ordinary CI:

`36438923685`

Single B256 read:

`queued`

Do not poll again in this bounce.

## Next fresh-bounce action

Read `36438923685` exactly once.

- success -> explicit STRATA-009 launch in a separate commit;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-009 launch.
No memory-control policy.
Proposal != Decision.
Expressibility != Executability.
