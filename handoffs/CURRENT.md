# CURRENT

> **Latest bounce:** B261
> **Stage:** REC-003 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

REC-003 implementation now exists for:

- file sizes 96 / 192 / 384 MiB
- 4 independent runner blocks
- fresh systemd unit per size
- 12 total trials
- no streaming workload
- no hot anonymous allocation

Measured phases:

- baseline
- after mmap
- after ctypes view
- after mincore vector allocation
- after mincore
- after resident count
- after cleanup
- after gc + settle

Each phase records memory.current and selected memory.stat fields.
Final memory.peak is also recorded.

Purpose: determine whether the sub-MiB post-scan floor trend in STRATA-007/008/009 is observer-induced.

Files:

- `specs/REC-003-RESIDENCY-OBSERVER-FOOTPRINT-v1.json`
- `src/finite_ram_lab/rec003_residency_observer.py`
- `.github/workflows/rec-003-residency-observer.yml`
- `tests/test_rec003_residency_observer.py`

No launch marker exists.

## Next fresh-bounce action

Discover/read B261 ordinary CI exactly once.

- success -> explicit REC-003 launch in a separate commit;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
