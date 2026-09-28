# CURRENT

> **Latest bounce:** B258
> **Stage:** STRATA-009 / HOSTED RUN LAUNCHED + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

Exact launch commit:

`01e73be662613d164f62287f126ef002c8ff234c`

Scientific run:

`36440093666`

Single B258 read:

`in_progress`

Do not poll again in this bounce.

Frozen study:
- Ubuntu 26.04
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 384 MiB
- DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 20 trials
- REC-001 98 records/trial
- buffered omitted

Question: can bounded streaming preserve the same knee when total dataset capacity exceeds MemoryMax?

Next fresh-bounce action: read run `36440093666` exactly once.

Hosted research only. No local-PC execution. No memory-control policy.
