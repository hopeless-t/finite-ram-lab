# CURRENT

> **Latest bounce:** B264
> **Stage:** REC-003 / HOSTED RUN LAUNCHED + EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Canonical scientific result

STRATA-009 run `36440093666`: PASS, 20/20.

96 / 192 / 384 MiB cold capacities share the same observed knee:

`80 < K <= 88 MiB`

including 384 MiB > MemoryMax 320 MiB.

Fine post-scan floor growth remains HOLD pending observer audit.

## REC-003

Exact launch commit:

`ce6866a92fc22bd09145c9837b1208023f801004`

Scientific run:

`36442276245`

Single B264 read:

`in_progress`

Do not poll again in this bounce.

Frozen execution:
- sizes 96 / 192 / 384 MiB
- 4 blocks
- 12 observer-only trials
- fresh systemd unit per size
- no streaming workload
- no hot anonymous allocation
- phase memory.current + memory.stat
- final memory.peak

Question: is the sub-MiB floor trend partly caused by the residency observer itself?

## Next fresh-bounce action

Read run `36442276245` exactly once.

- success -> fetch aggregate once and validate/atomize 12 trials;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
