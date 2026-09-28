# Bounce Handoff

> **Bounce ID:** B236
> **Status:** COMPLETE / STRATA-006 LIVE-SET HEADROOM DESIGN FROZEN

## Parent result

STRATA-005 canonical PASS:

- run `36431449193`
- 40 / 40 trials
- fixed raw-MiB knee rejected for tested pressure configurations
- additive effective-live-set headroom model remains feasible with `B in [72, 80) MiB`

## Council decision

The next highest-information experiment varies hot/live-set size while holding pressure constant.

Frozen STRATA-006:

- MemoryHigh: 160 MiB
- MemoryMax: 320 MiB
- hot anon: 56 / 72 MiB
- existing 64 MiB hot-anon STRATA-004 result retained as anchor
- cold file: 96 MiB
- read chunk: 4 MiB
- arms: buffered + DONTNEED 64 / 72 / 80 / 88 / 96 MiB
- 4 blocks per new hot setting
- 48 new hosted trials
- Recorder density unchanged

Mechanism discriminator:

`K + hot_anon ~= constant`

versus a fixed raw `K`.

## Monte Carlo

Deferred until live-set-axis observations exist.

## Next action

Implement STRATA-006 spec/scheduler/aggregator/workflow/tests only.

Implementation does not grant launch authority.

## Authority boundary

Hosted repository/research work only.
No local-PC execution.
No STRATA-006 launch yet.
No memory-control policy authorized.
Proposal != Decision.
Expressibility != Executability.
