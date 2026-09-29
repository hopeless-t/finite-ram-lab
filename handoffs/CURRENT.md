# CURRENT

> **Latest bounce:** B352
> **Stage:** MEMCG-005F IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## MEMCG-005E

Canonical:
`a0254e7d8b4348986a0d9fe034e94ecdb47a0255`

Decision:
`REJECT_BASELINE_GATE`

Key secondary:
REMOTE_S LOW = 89/90 Q64.

## MEMCG-005F

Implementation files:
- `specs/MEMCG-005F-REMOTE-LOW-ADMISSION-GATE-v1.json`
- `src/finite_ram_lab/memcg005f_remote_low_gate.py`
- `.github/workflows/memcg-005f-remote-low-gate.yml`
- `tests/test_memcg005f_remote_low_gate.py`

Worker unchanged:
`experiments/memcg005d_worker.c`

Primary gate:
`REMOTE_LOW := startup P, measured S!=P, pre_current_pages<=110`

Scale:
64 identities/block x4 =256 probes.

No launch marker exists.

## Next fresh-bounce action

Discover/read ordinary CI exactly once.

- success -> explicit MEMCG-005F launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
No Remote Desktop Commander.
