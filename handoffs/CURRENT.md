# CURRENT

> **Latest bounce:** B347
> **Stage:** MEMCG-005E IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## MEMCG-005D accepted result

Canonical:
`8878b1dc047c9bac690c6cce7094ea6b6b44ee32`

Decision:
`REJECT_EXTERNAL_PATH`

## MEMCG-005E

Prospective threshold:
`LOW iff pre_current_pages <= 110`

Implementation files:
- `specs/MEMCG-005E-BASELINE-STRATIFIED-FIRST-TOUCH-v1.json`
- `src/finite_ram_lab/memcg005e_baseline_stratified.py`
- `.github/workflows/memcg-005e-baseline-stratified.yml`
- `tests/test_memcg005e_baseline_stratified.py`

Worker:
reuses exact `experiments/memcg005d_worker.c`.

Arms:
- LOCAL_P
- REMOTE_S

32 identities per arm per block.
4 blocks.
256 probes.

No launch marker exists.

## Next fresh-bounce action

Discover/read ordinary CI for B347 exactly once.

- success -> explicit MEMCG-005E hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
