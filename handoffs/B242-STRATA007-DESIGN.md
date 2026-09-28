# Bounce Handoff

> **Bounce ID:** B242
> **Status:** COMPLETE / STRATA-007 CROSS-IMAGE DESIGN FROZEN

## Parent mechanism

STRATA-006 directly replicated the live-set mechanism:

- hot=56 -> `88 < K <= 96`
- hot=64 anchor -> `80 < K <= 88`
- hot=72 -> `72 < K <= 80`

all mapping to:

`144 < K+hot <= 152 MiB`.

## Council decision

Next axis: hosted software substrate/image.

Frozen STRATA-007:

- new runner: `ubuntu-26.04`
- anchor: existing Ubuntu 24.04 STRATA-004 evidence
- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- hot anon: 64 MiB
- cold file: 96 MiB
- read chunk: 4 MiB
- Python requested: 3.12
- arms: buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 new trials
- REC-001: 26 records/trial

Primary portability discriminator:

Does Ubuntu 26.04 remain compatible with `80 < K <= 88` and `144 < K+hot <= 152`?

## Next action

Implement STRATA-007 only.

Do not launch in the implementation bounce.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-007 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
