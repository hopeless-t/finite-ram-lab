# CURRENT

> Latest bounce: B362
> Stage: MEMCG-005G-B IMPLEMENTED / CI PENDING
> Stop: CI_DISCOVERY_PENDING

Design:
`docs/MEMCG-005G-B-BIOPSY-FOOTPRINT-CONTROL-v1.md`

Implementation:
- `specs/MEMCG-005G-B-BIOPSY-FOOTPRINT-CONTROL-v1.json`
- `src/finite_ram_lab/memcg005gb_footprint_control.py`
- `.github/workflows/memcg-005g-b-footprint-control.yml`
- `tests/test_memcg005gb_footprint_control.py`

Primary:
CAP70 vs CAP8 first-touch failure among valid REMOTE_LOW.

Scale:
16 independent blocks x64 candidates =1024.

No biopsy in primary A/B.
No launch marker exists.

Next fresh bounce:
discover/read ordinary CI exactly once.

Hosted research only.
No local-PC execution.
