# CURRENT

> **Latest bounce:** B267
> **Stage:** REC-004 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## REC-004 implementation

Exact hygiene contract:

- external cold verification outside measured cgroup;
- no pre-scan mincore inside measured unit;
- scan at DONTNEED 64 MiB;
- capture `post_scan_pre_observer`;
- run historical `_file_residency()`;
- capture `post_scan_post_observer`.

Matrix:
- Ubuntu 26.04
- file sizes 96 / 192 / 384 MiB
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- 4 blocks
- 12 trials

Primary paired metric:

`observer_current_delta = post_observer - pre_observer`

No launch marker exists.

Files:
- `specs/REC-004-PREPOST-OBSERVER-HYGIENE-v1.json`
- `src/finite_ram_lab/rec004_prepost_observer_hygiene.py`
- `.github/workflows/rec-004-prepost-observer.yml`
- `tests/test_rec004_prepost_observer_hygiene.py`

## Next fresh-bounce action

Discover/read B267 ordinary CI exactly once.

- success -> explicit REC-004 launch in a separate commit;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
