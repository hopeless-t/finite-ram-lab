# CURRENT

> **Latest bounce:** B243
> **Stage:** STRATA-007 IMPLEMENTED / CI PENDING
> **Turn stop reason:** CI_DISCOVERY_PENDING

## Canonical mechanism

STRATA-006 run `36434232753`: PASS, 48/48.

At MemoryHigh=160 MiB:

- hot56 -> `88 < K <= 96`
- hot64 anchor -> `80 < K <= 88`
- hot72 -> `72 < K <= 80`

All map to:

`144 < K+hot <= 152 MiB`.

## STRATA-007

Portability implementation now exists for:

- runner `ubuntu-26.04`
- explicit Python 3.12
- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- hot anon 64 MiB
- cold file 96 MiB
- buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks
- 24 trials
- same Recorder density

Primary question:

Does the Ubuntu 26.04 onset remain compatible with the Ubuntu 24.04 anchor:

`80 < K <= 88`

and:

`144 < K+hot <= 152`?

Files:

- `docs/STRATA-007-CROSS-IMAGE-v1.md`
- `specs/STRATA-007-CROSS-IMAGE-v1.json`
- `src/finite_ram_lab/strata007_cross_image.py`
- `.github/workflows/strata-007-cross-image.yml`
- `tests/test_strata007_cross_image.py`

No launch marker exists.

## Monte Carlo

Deferred until STRATA-007 observations exist.

## Next fresh-bounce action

Discover/read B243 ordinary CI exactly once.

- success -> explicit STRATA-007 launch in a new bounce;
- pending/in_progress -> EXTERNAL_WAIT;
- failure -> inspect only the exposed invariant.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state
- LLM-jp-4.1 local worker + state-lifetime dogfood

No local execution is authorized.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-007 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
