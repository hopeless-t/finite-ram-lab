# Bounce Handoff

> **Bounce ID:** B204
> **Status:** EXTERNAL_WAIT / STRATA-004 IMPLEMENTED AND LAUNCHED

## Implemented

Added STRATA-004-specific hosted research surfaces without modifying the historical STRATA-003 frozen contract:

- `src/finite_ram_lab/strata004_knee_workload.py`
- `src/finite_ram_lab/strata004_knee_study.py`
- `tests/test_strata004_knee.py`
- `.github/workflows/strata-004-knee.yml`

The copied collector initially retained STRATA-003 directory globs. Readback caught this before launch and commit `80c21a4bb874229c52ead61c043c87636c5e32ab` corrected the collector to STRATA-004 paths.

## Launch

Launch commit:

`4d22de0570030c987db3e76416c009e67c58341a`

One status read was performed, per relay rule.

Observed:

- STRATA-004 Knee v1 run: `36392457515`
- status: `queued`
- ordinary CI run: `36392457516`
- status: `in_progress`

No rerun or polling loop was performed.

## Frozen study

- 8 runner blocks
- buffered + DONTNEED 32 / 48 / 64 / 72 / 80 / 88 / 96 MiB
- 64 total trials
- pressure/capacity primary
- throughput secondary
- kernel / OS / systemd / cgroup provenance captured per block

## Next fresh-turn action

Read STRATA-004 run `36392457515` exactly once.

- success -> inspect aggregate artifact once and canonicalize the response surface
- pending -> checkpoint EXTERNAL_WAIT again and stop
- failure -> inspect the failed run only; no blind rerun

Ordinary CI `36392457516` may be read alongside that fresh-turn observation, but its state does not authorize a targeted rerun.

## Authority boundary

Hosted research only.
No local-PC execution.
No rerun/retry authority inferred.
No OSS default cadence authorized.
