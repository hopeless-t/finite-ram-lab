# CURRENT

> **Latest bounce:** B327
> **Stage:** MEMCG-005B IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## MEMCG-005

Canonical:
`95191357ac80b9157c2f9f05df86672abb661983`

Decision:
`INCONCLUSIVE`

## MEMCG-005B implementation

Files:
- `specs/MEMCG-005B-THREE-CPU-STAGED-K7-v1.json`
- `experiments/memcg005b_worker.c`
- `src/finite_ram_lab/memcg005b_staged_k7.py`
- `src/finite_ram_lab/memcg005b_runner.py`
- `.github/workflows/memcg-005b-staged-k7.yml`
- `tests/test_memcg005b_staged_k7.py`

CPU roles:
- C controller
- P prep
- S stock-test

No participant touches S before measured insertion.

Prefill:
14 distinct verified wash insertions before target.

Source signature:
0/5/6 PRESENT; 7/8 ABSENT.

No launch marker exists.

## Next fresh-bounce action

Discover/read ordinary CI for B327 exactly once.

- success -> explicit MEMCG-005B launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
