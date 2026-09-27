# Bounce Handoff

> **Bounce ID:** B187
> **Status:** COMPLETE / STRATA-002 MEMORY-EFFICIENCY METRICS FROZEN

## New metric set

- Resident Footprint Reduction (RFR)
- Cold-Stream Amplification Factor (CSAF)
- Recovered Memory Headroom (RMH / NRH)
- Cold Cache Retention Fraction (CCRF)
- Pressure Event Suppression (PES)
- Scan-Time Cost Ratio (SCR)

## Current strongest descriptive values

DONTNEED vs ordinary buffered:

- paired median resident-footprint reduction: 52.13%
- median saved footprint: ~82.98 MiB
- recovered headroom under MemoryHigh=160 MiB: ~83.46 MiB
- buffered CSAF vs direct: ~2.10x
- DONTNEED CSAF vs direct: ~1.00x
- high-event suppression: 100% in 8/8 blocks
- COLD file residency: ~86.5% -> 0%
- median scan ratio: 1.027x, but highly variable

## Boundary

These are workload-footprint metrics, not claims of 52% total-system RAM savings.

## Parallel external state

STRATA-002 confirmatory design MC was launched in B186 and is externally pending.

## Next action

When MC completes, use its result plus these metrics to decide hosted confirmation vs local external-validity dogfood.

## Authority boundary

Design/research only.
