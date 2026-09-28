# CURRENT

> **Latest bounce:** B282
> **Stage:** MEMCG-001 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## MEMCG-001 implementation

Files:
- `specs/MEMCG-001-PAGE-CHARGE-QUANTIZATION-v1.json`
- `experiments/memcg001_worker.c`
- `src/finite_ram_lab/memcg001_quantization.py`
- `.github/workflows/memcg-001-quantization.yml`
- `tests/test_memcg001_quantization.py`

Measurement:
- fresh systemd cgroup per trial
- C worker
- fixed CPU affinity
- 4096-byte page requirement
- 256 samples after one-page touch increments
- identical no-touch control
- 4 blocks / 8 trials

Math:
- baseline-corrected current pages
- first differences
- significant jump extraction
- candidate Q={1,2,4,8,16,32,64,128}
- magnitude lattice score
- modulo phase concentration
- jump spacing
- autocorrelation
- preregistered H64 decision

No launch marker exists.

## Next fresh-bounce action

Discover/read B282 ordinary CI exactly once.

- success -> explicit MEMCG-001 hosted launch;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only exposed invariant.

## LDC path

If hosted result is stable, prepare a separate MVCA-bound local replication using the same C worker/analyzer on Lubuntu.

No local execution in current bounce.

## Authority boundary

Hosted repository/research only.
No local-PC execution.
No memory-control policy.
