# B387 — Controlled spawn result + retrospective pause

## Status

RESEARCH PAUSE / SYNTHESIS COMPLETE.

No new physical run launched after controlled-spawn v2.

## Controlled-spawn v2

Run:
`36595481746 = success`

Execution:
- 8/8 blocks PASS
- 72/72 frozen identities executed
- 0 replacements
- 0 CPU mismatches
- 0 worker errors
- 0 geometry violations
- 0 measured VmPTE growth across 4,164 measured touches

Frozen strict primary:
- b62: 22/24 exact
- b63: 11/24 exact
- b64: 16/24 exact
- overall: 49/72 exact

Direct Q64 primer found:
- 55/72

Post-primer arm phase:
- b62: 23/23 exact terminal pattern
- b63: 14/14 exact terminal pattern
- b64: 18/18 exact terminal pattern
- overall: **55/55**

Do not replace the frozen 49/72 endpoint with 55/55.
The latter is a secondary mechanistic observation.

## Accounting contamination

All 17 calibration OTHER deltas:
`-17 pages`

All 6 BAIT_NONZERO trials had negative deltas only and nevertheless ended in the exact predicted terminal phase.

Linux v7.0 `drain_stock()` directly uncharges the exact cached stock page count.

Hypothesis:
negative deltas are accounting/uncharge events rather than S-CPU stock consumption.

Not yet proven.

## Evidence

Raw:
- 152 files
- 1,705,625 bytes
- content-set SHA:
  `e65281ad34ac9f8c0eaf366d2b35ccb07404f8fdf246bfeea4cbcd4d1c0602fd`

Drive COLD:
`Catfood Lab Evidence/finite-ram-lab/MEMCG-005G-C-v2/run-36595481746`

9/9 archive ZIPs:
`BYTE-IDENTICAL PASS`

## Retrospective

`docs/RETROSPECTIVE-001-Q64-TO-SPAWN.md`

Main conceptual transition:

`rare-event hunting -> hidden-state inference -> controlled state construction`

High confidence:
- Q64 memcg batch/stock mechanism
- per-CPU stock state
- PTE stock consumption path
- PTE preconditioning effectiveness
- post-primer b62/b63/b64 phase arithmetic
- argv-width explanation rejected

Remaining:
- primer acquisition cleanliness
- exact source of -17 uncharge
- natural 9-12 capacity trigger
- reliability certification

## Strata intake

Observed:
`Niko1221/Strata @ 3ce2523c2823687de5372be3af58534f56cbf286`

Intake:
`docs/STRATA-001-EXTERNAL-INTAKE.md`

Relevant patterns:
- VRAM/RAM/SSD tiered residency
- expert working-set profiling + online adaptation
- leaseable expert-cache slots for prefill scratch
- bounded pinned-memory staging rings
- SSD read dedup/reordering
- cross-class substitution (KV down-tier -> expert up-tier)
- bottleneck shift after cache saturation
- slower extra device can make total system worse

## Stop

Human review / retrospective discussion.

Do not launch another physical experiment until after this review.
