# Bounce Handoff

> **Bounce ID:** B237
> **Status:** COMPLETE / STRATA-006 IMPLEMENTED / NOT LAUNCHED

## Frozen parent design

B236 froze STRATA-006 as a fixed-pressure, variable-live-set mechanism test.

## Implementation

Added:

- `specs/STRATA-006-LIVESET-HEADROOM-v1.json`
- `src/finite_ram_lab/strata006_liveset_headroom.py`
- `.github/workflows/strata-006-liveset-headroom.yml`
- `tests/test_strata006_liveset_headroom.py`

The implementation preserves:

- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 56 / 72 MiB
- 96 MiB cold file
- 4 MiB read chunks
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks per hot setting
- 48 total trials
- REC-001 at 26 records/trial

The workflow is path-gated by `launch/STRATA-006-v1.txt`.

No launch marker exists in this bounce.

## Analysis contract

The aggregate reports:

- raw onset by hot-anon setting
- `K + hot` interval
- effective floor interval
- non-hot floor interval
- full matrix validity

The existing STRATA-004 hot=64 anchor is metadata only and is not duplicated as new evidence.

## Safety regression

The trial systemd boundary uses an absolute spec path through `$GITHUB_WORKSPACE`, preserving the B231 portability repair.

## Monte Carlo

Deferred until physical STRATA-006 observations exist.

## Next action

Read ordinary CI for B237 exactly once.

- success -> create explicit STRATA-006 launch marker in a separate bounce;
- pending -> checkpoint EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-006 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
