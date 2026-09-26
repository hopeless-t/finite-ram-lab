# Bounce Handoff

> **Bounce ID:** B018  
> **Status:** COMPLETE

## Objective

Read EXP-001 using only the frozen analysis and record the causal result.

## Evidence

- run: `36228194951`;
- 8 independent runner blocks;
- 32 valid trials;
- exact `2^8` block sign-flip inference.

Primary result:

    HOT_EVICT / COLD_EVICT geometric mean latency ratio = 639.45x
    exact two-sided p = 0.0078125
    cluster-bootstrap 95% ratio interval = [390.37x, 1125.54x]

Arm medians:

    HOT_EVICT  = 121.647 ms
    COLD_EVICT =   0.261 ms

Intervention fidelity:

    max target residency = 0.09375
    min non-target residency = 1.0

## Frozen finding

Residency identity relative to imminent application demand is causally important in the bounded experiment even when reclaimed quantity is matched.

## Next recommended bounce

> Run a fresh pseudo-Council on the smallest existing Linux application hint that can test whether semantic information improves **natural** transition-zone reclaim behavior.

Preferred first candidate: `MADV_COLD` on the not-soon-needed semantic region, not a new coordinator.

Use a capability/calibration step if the hint's effect on this hosted environment is uncertain.

## Authority boundary

EXP-001 validates causal importance of residency alignment. It does not establish natural kernel suboptimality or a production architecture.
