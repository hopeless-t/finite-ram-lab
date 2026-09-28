# CURRENT

> **Latest bounce:** B262
> **Stage:** REC-003 IMPLEMENTED + CI EXTERNAL_WAIT
> **Turn stop reason:** EXTERNAL_WAIT

## Canonical scientific result

STRATA-009 run `36440093666`: PASS, 20/20.

Cold dataset 384 MiB exceeded MemoryMax 320 MiB while bounded DONTNEED streaming preserved:

`80 < K <= 88 MiB`

with no OOM.

96 / 192 / 384 MiB therefore share the same observed knee.

## Fine-floor measurement caveat

Post-scan non-hot floor increased slightly across capacities, but `_file_residency()` mmaps the full file and runs mincore before memory.current is captured.

Fine floor growth remains HOLD pending REC-003.

## REC-003 implementation

Exact commit:

`a9eaf6a384eccb86a9c59b6e8d072cbb7f371a47`

Observer-only 96 / 192 / 384 MiB audit:

- 4 blocks
- 12 trials
- fresh systemd unit per size
- no streaming
- no hot anon
- phase memory.current + memory.stat
- final memory.peak

CI:

`36441838606`

Single B262 read:

`in_progress`

Do not poll again in this bounce.

## Next fresh-bounce action

Read `36441838606` exactly once.

- success -> explicit REC-003 launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
