# CURRENT

> Latest bounce: B357
> Stage: MEMCG-005G-A IMPLEMENTED / CI PENDING
> Stop: CI_DISCOVERY_PENDING

Design:
`docs/MEMCG-005G-A-EARLY-TRANSIENT-BIOPSY-v1.md`

Implementation:
- `specs/MEMCG-005G-A-EARLY-TRANSIENT-BIOPSY-v1.json`
- `src/finite_ram_lab/memcg005g_early_biopsy.py`
- `.github/workflows/memcg-005g-a-early-biopsy.yml`
- `tests/test_memcg005g_early_biopsy.py`

Primary fixed boundary:
EARLY identity 0..7
STEADY identity 8..31

24 independent blocks x32 candidates =768.

Failure biopsy:
valid REMOTE_LOW first-touch zero -> continue fresh touches through total touch65, recording first next Q64 as residual_depth_candidate.

No launch marker exists.

Next fresh bounce:
discover/read ordinary CI exactly once.

Hosted research only.
No local-PC execution.
