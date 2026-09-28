# CURRENT

> **Latest bounce:** B249
> **Stage:** STRATA-008 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## STRATA-008 implementation

Exact implementation adds:

- `specs/STRATA-008-COLD-CAPACITY-v1.json`
- `src/finite_ram_lab/strata008_cold_capacity.py`
- `.github/workflows/strata-008-cold-capacity.yml`
- `tests/test_strata008_cold_capacity.py`

Frozen study:

- Ubuntu 26.04
- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 192 MiB
- read chunk 4 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 total trials

Recorder records/trial = 50 because 192 MiB / 4 MiB = 48 scan checkpoints plus start/end.

Environment receipt now uses `systemd-run --version`.

No launch marker exists.

## Next fresh-bounce action

Discover/read B249 ordinary CI exactly once.

- success -> explicit STRATA-008 launch in a separate commit;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No STRATA-008 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
