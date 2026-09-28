# CURRENT

> **Latest bounce:** B237
> **Stage:** STRATA-006 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## Parent result

STRATA-005 run `36431449193`: PASS, 40/40.

Canonical interpretation:

- fixed raw-MiB knee rejected for tested pressure configurations;
- additive effective-live-set headroom remains supported directionally;
- no controller formula or OSS default authorized.

## STRATA-006

Frozen question:

At MemoryHigh=160 MiB, does changing hot/live-set size move the DONTNEED knee inversely?

Implementation now exists for:

- hot anon 56 / 72 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks per hot setting
- 48 total trials
- Recorder 26 records/trial

Primary transformed discriminator:

`K + hot_anon ~= constant`

against fixed raw `K`.

Files:

- `docs/STRATA-006-LIVESET-HEADROOM-v1.md`
- `specs/STRATA-006-LIVESET-HEADROOM-v1.json`
- `src/finite_ram_lab/strata006_liveset_headroom.py`
- `.github/workflows/strata-006-liveset-headroom.yml`
- `tests/test_strata006_liveset_headroom.py`

Workflow launch is gated by:

`launch/STRATA-006-v1.txt`

No launch marker has been created.

## Monte Carlo

Deferred until STRATA-006 observations exist.

## Next fresh-bounce action

Discover/read B237 ordinary CI exactly once.

- success -> explicit STRATA-006 launch marker in a separate commit;
- pending/in_progress -> checkpoint EXTERNAL_WAIT and stop;
- failure -> inspect only the exposed invariant.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state study
- LLM-jp-4.1 local-worker + state-lifetime dogfood

No local execution is authorized for either.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-006 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
