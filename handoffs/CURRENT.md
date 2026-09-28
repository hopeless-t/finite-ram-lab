# CURRENT

> **Latest bounce:** B307
> **Stage:** MEMCG-003B IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## MEMCG-003B implementation

Files:
- `specs/MEMCG-003B-NONCONSUMING-SEVEN-SLOT-v1.json`
- `src/finite_ram_lab/memcg003b_nonconsuming.py`
- `.github/workflows/memcg-003b-nonconsuming.yml`
- `tests/test_memcg003b_nonconsuming.py`

Worker:
reuses `experiments/memcg003_holder.c`.

Repairs:
- passive target observation only during churn;
- no target touches during threshold estimation;
- one final target touch;
- control CPU and stock CPU separated.

Primary threshold:
`E_drop = first passive target memory.current drop >=16 pages`

Candidate K:
`1..10`

No launch marker exists.

## pmndrs/math

MATH-002 remains frozen and waits for MEMCG-003B clean data.

## Next fresh-bounce action

Discover/read B307 ordinary CI exactly once.

- success -> explicit MEMCG-003B launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
