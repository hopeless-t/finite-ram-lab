# CURRENT

> **Latest bounce:** B236
> **Stage:** STRATA-006 LIVE-SET HEADROOM DESIGN FROZEN
> **Turn stop reason:** READY_FOR_IMPLEMENTATION

## Canonical STRATA-005 result

Run `36431449193`: PASS, 40 / 40 trials.

Observed onset:

- H=144: `64 < K <= 80`
- H=160 anchor: `80 < K <= 88`
- H=176: `K > 96`

Fixed raw cadence is not consistent across the tested pressure settings.

Additive interpretation:

`K = H - B`

with common feasible:

`B in [72, 80) MiB`

and observed STRATA-005 DONTNEED post-scan floor around `76.72 MiB`.

## STRATA-006 frozen design

Question: at fixed MemoryHigh, does changing hot/live-set size move the knee inversely?

Constants:

- MemoryHigh 160 MiB
- MemoryMax 320 MiB
- cold file 96 MiB
- read chunk 4 MiB
- same hosted runner family and DONTNEED implementation
- same Recorder density

New hot-anon settings:

- 56 MiB
- 72 MiB

Reuse STRATA-004 hot=64 MiB as anchor.

Arms:

- buffered
- DONTNEED 64 / 72 / 80 / 88 / 96 MiB

Budget:

- 2 x 6 x 4 = 48 new hosted trials

Primary discriminator:

`K + hot_anon ~= constant`

versus fixed raw `K`.

Frozen design document:

`docs/STRATA-006-LIVESET-HEADROOM-v1.md`

## Monte Carlo

Deferred until STRATA-006 observations exist.

## Queued future studies

- Naive-N0.5-Flash semantic reuse / reconstructible-state study
- LLM-jp-4.1 local-worker + state-lifetime dogfood

They are proposals and do not authorize local execution.

## Next fresh-bounce action

Implement STRATA-006:

- machine-readable spec
- deterministic schedule
- trial wrapper using REC-001
- aggregate validation
- hosted workflow
- regression tests

Do not launch in the implementation bounce.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-006 launch.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
