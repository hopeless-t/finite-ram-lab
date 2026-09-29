# CURRENT

> **Latest bounce:** B320
> **Stage:** MEMCG-005 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## Accepted primitive

MEMCG-004:
`SUPPORT_CALIBRATED_STOCK`

Calibrated R:
`[64,64,64,64]`

## MEMCG-005 implementation

Files:
- `specs/MEMCG-005-CALIBRATED-K7-v1.json`
- `experiments/memcg005_worker.c`
- `src/finite_ram_lab/memcg005_calibrated_k7.py`
- `src/finite_ram_lab/memcg005_runner.py`
- `.github/workflows/memcg-005-calibrated-k7.yml`
- `tests/test_memcg005_calibrated_k7.py`

Per replica:
- prestart 16 worker identities;
- normalize each to EMPTY by observed +64 then 63 consumptions;
- require next measured insertion touch to be +64;
- insert W0..W6;
- insert target;
- insert C1..Cm;
- one-shot target probe;
- terminate replica.

Independent m:
`{0,5,6,7,8}`

Source K7 signature:
- m0/5/6 PRESENT
- m7/8 ABSENT

Model candidate K:
`1..9`

Sparse observational equivalence classes are reported explicitly.

PRESENT operationalization:
`abs(target_probe_delta) < 16 pages`

No launch marker exists.

## Next fresh-bounce action

Discover/read ordinary CI for B320 exactly once.

- success -> explicit MEMCG-005 launch in a separate bounce;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
