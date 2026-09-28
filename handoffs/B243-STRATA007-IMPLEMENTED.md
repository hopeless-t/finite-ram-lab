# Bounce Handoff

> **Bounce ID:** B243
> **Status:** COMPLETE / STRATA-007 IMPLEMENTED / NOT LAUNCHED

## Parent design

B242 froze one new Ubuntu 26.04 portability screen against the existing Ubuntu 24.04 STRATA-004 anchor.

## Implementation

Added:

- `specs/STRATA-007-CROSS-IMAGE-v1.json`
- `src/finite_ram_lab/strata007_cross_image.py`
- `.github/workflows/strata-007-cross-image.yml`
- `tests/test_strata007_cross_image.py`

Frozen execution:

- runner `ubuntu-26.04`
- Python requested explicitly: 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 96 MiB
- read chunk 4 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 total trials
- REC-001 density unchanged

Environment receipts include kernel, systemd, cgroup filesystem, OS release, and runner image variables.

Launch remains gated by:

`launch/STRATA-007-v1.txt`

No marker exists in this bounce.

## Monte Carlo

Deferred until cross-image physical observations exist.

## Next action

Read ordinary CI for B243 exactly once.

- success -> explicit STRATA-007 launch in a separate bounce;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-007 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
