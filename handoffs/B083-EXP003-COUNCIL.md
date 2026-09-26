# Bounce Handoff

> **Bounce ID:** B083
> **Status:** COMPLETE / EXP-003 COUNCIL CONVERGED

## Objective

Choose the bounded intervention question and the method for sizing EXP-003.

## Council result

EXP-003 will test the existing 16 MiB MADV_PAGEOUT preparation only as a mechanism probe at the independently justified 160–162 MiB high-headroom regime.

Frozen conceptual factors:

- MemoryHigh 160 / 162 MiB
- shared-VMA initial fault order
- independent future HOT position
- CORRECT_PAGEOUT / NO_HINT / WRONG_PAGEOUT

Primary benefit question:

> In naturally misaligned trials, does CORRECT_PAGEOUT reduce HOT-retouch latency versus NO_HINT?

Total action-to-HOT interval remains mandatory for net-benefit classification.

Aligned trials remain as a control stratum.

## Design sizing

Runner/repeat allocation is NOT frozen.

A design Monte Carlo must compare D1-D5 using empirical HYP-003 block structure and separate EXP-002 Red-Team/action-cost calibration.

## Next recommended bounce

Snapshot the minimum HYP-003 and EXP-002 empirical inputs needed for the EXP-003 design Monte Carlo, with provenance, then stop.

## Authority boundary

No EXP-003 experiment is authorized yet.
