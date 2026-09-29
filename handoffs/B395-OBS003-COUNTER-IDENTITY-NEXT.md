# B395 — OBS-003 closes stock-drain branch for dominant -17 and exposes counter-identity ambiguity

## Status

OBS-003 COMPLETE / CORRECTED DERIVED INTERPRETATION / EVIDENCE COLD-VERIFIED.

Run:
\`36620215583\`

## Direct result

48 trials / 1,152 measured touches.

Exact -17:
13

Frozen aggregate:
- LRU_BATCH 12
- OTHER_STACK 1
- STOCK_DRAIN 0

Corrected interpretation:
- WORKER_LRU_BATCH 12
- UNRESOLVED_COUNTER_IDENTITY 1
- STOCK_DRAIN 0

## Why OTHER_STACK was corrected

The one apparent OTHER_STACK event was executed by:

\`.NET Tiered Com\`

through a shmem fault path.

The worker runs in a dedicated systemd service cgroup.

Time coincidence alone cannot prove that the .NET page_counter_uncharge changed the worker's memory.current.

Therefore the event remains unresolved until page_counter pointer identity is matched.

## Stock-drain branch

No exact -17 specimen has direct stock-drain attribution.

A separate -1 observation overlaps drain/refill activity, proving such activity can contaminate memory.current observations.

Do not generalize that -1 event into the -17 mechanism.

## Dominant mechanism

Across OBS-002 + OBS-003:

- direct worker LRU-batch exact -17: 21
- exact -17 total: 24

Descriptive only.

The dominant observed -17 mechanism remains:

\`LRU batch fill -> flush31 -> folios_put -> page_counter_uncharge17\`

## Evidence

Raw:
- 124 files
- 7,480,253 bytes
- content-set SHA:
  \`a0b5e7aa538778f5ac295e22b475ebf8fcfbe5f959f830af51b57f7cc2b4f67a\`

Drive:
\`Catfood Lab Evidence/finite-ram-lab/OBS-003-RESIDUAL-17-CALLER-v1/run-36620215583\`

5/5 BYTE-IDENTICAL PASS.

## Next

OBS-004:

Page-counter identity correlation.

Require:
- worker page_counter_try_charge counter pointer
- system-wide page_counter_uncharge17 counter pointer
- pointer equality before caller attribution

No b63 reliability scaling yet.
