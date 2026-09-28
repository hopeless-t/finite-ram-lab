# CURRENT

> **Latest bounce:** B255
> **Stage:** STRATA-009 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## STRATA-009 implementation

Exact implementation contains:

- `specs/STRATA-009-DATASET-GT-MEMORYMAX-v1.json`
- `src/finite_ram_lab/strata009_dataset_gt_memorymax.py`
- `.github/workflows/strata-009-dataset-gt-memorymax.yml`
- `tests/test_strata009_dataset_gt_memorymax.py`

Frozen study:

- Ubuntu 26.04
- Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 384 MiB
- read chunk 4 MiB
- DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 20 trials
- REC-001 98 records/trial
- buffered intentionally omitted

Question:

Can total one-shot dataset capacity exceed MemoryMax while bounded streaming remains below the same instantaneous-memory knee?

No launch marker exists.

## Next fresh-bounce action

Discover/read B255 ordinary CI exactly once.

- success -> explicit STRATA-009 launch in a separate commit;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No STRATA-009 launch.
No memory-control policy.
Proposal != Decision.
Expressibility != Executability.
