# Bounce Handoff

> **Bounce ID:** B248
> **Status:** COMPLETE / STRATA-008 COLD-CAPACITY DESIGN FROZEN

## Parent result

STRATA-007 cross-image PASS:

- Ubuntu 26.04, 24/24 trials
- `80 < K <= 88 MiB`
- `144 < K+hot <= 152 MiB`
- DONTNEED non-hot floor median 12.8125 MiB

## Frozen STRATA-008

New axis:

- cold file: 192 MiB

Constants:

- runner Ubuntu 26.04
- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- read chunk 4 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 total new trials
- REC-001 density unchanged

Reuse STRATA-007 96 MiB cold-file result as anchor.

Primary question:

Does doubling total one-shot cold capacity leave knee and retained floor bounded?

## Recorder repair

New workflow must capture systemd version using `systemd-run --version`.

## Next action

Implement STRATA-008 only.
Do not launch in the implementation bounce.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-008 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
