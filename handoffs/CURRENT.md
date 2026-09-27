# CURRENT

> **Latest bounce:** B188
> **Stage:** STRATA-002 / EFFICIENCY METRICS FROZEN + CONFIRMATORY MC PENDING
> **Turn stop reason:** EXTERNAL_WAIT

## Frozen practical metrics

DONTNEED vs buffered:

- Resident Footprint Reduction median: 52.13%
- median saved footprint: 82.98 MiB
- recovered MemoryHigh headroom: 83.46 MiB
- cold-stream amplification: 2.10x -> ~1.00x
- high-event suppression: 8/8 blocks
- COLD file residency: ~86.5% -> 0%

See:

- `docs/STRATA-002-MEMORY-EFFICIENCY-METRICS-v1.md`
- `evidence/STRATA-002-PILOT/efficiency-metrics-v1.json`

## Pending external run

- confirmatory design MC: `36339291206`
- last observed status: `queued`

## Next fresh-turn action

Read MC run `36339291206` exactly once.

## Authority boundary

Design/research only.
