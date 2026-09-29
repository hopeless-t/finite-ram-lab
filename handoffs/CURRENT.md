# CURRENT

> Latest bounce: B395
> Stage: DOMINANT -17 = WORKER LRU/FOLIO-BATCH RELEASE / ONE COUNTER-IDENTITY RESIDUAL
> Stop: READY FOR OBS-004 PAGE-COUNTER IDENTITY CORRELATION

## OBS-003

Run:
\`36620215583 = success\`

Scale:
- 48 trials
- 1152 touches

Exact -17:
13

Frozen aggregate:
- LRU_BATCH 12
- OTHER_STACK 1
- STOCK_DRAIN 0

Corrected derived interpretation:
- WORKER_LRU_BATCH 12
- UNRESOLVED_COUNTER_IDENTITY 1
- STOCK_DRAIN 0

The unresolved event:
- trial 3:1
- touch23
- start115
- coincident system-wide page_counter_uncharge17
- comm = .NET Tiered Com
- shmem-fault LRU stack
- no worker LRU flush/folios_put
- block3 relevant probe misses = 0

Because worker runs in a dedicated systemd service cgroup,
time coincidence alone is insufficient.

## Dominant mechanism

Across OBS-002 + OBS-003, descriptive:
21/24 exact -17 have direct worker LRU-batch chain.

## Evidence

OBS-003 raw:
- files 124
- bytes 7,480,253
- SHA:
  \`a0b5e7aa538778f5ac295e22b475ebf8fcfbe5f959f830af51b57f7cc2b4f67a\`

Drive:
\`Catfood Lab Evidence/finite-ram-lab/OBS-003-RESIDUAL-17-CALLER-v1/run-36620215583\`

Verification:
5/5 BYTE-IDENTICAL PASS

## Next

OBS-004 page-counter identity correlation.

Caller attribution requires:
1. worker page_counter_try_charge pointer
2. candidate page_counter_uncharge17 pointer
3. pointer equality

Classes:
- WORKER_LRU_BATCH
- SAME_COUNTER_ASYNC
- STOCK_DRAIN_SAME_COUNTER
- EXTERNAL_COINCIDENCE
- COUNTER_UNKNOWN
- TRACE_MISS

## Authority

HOSTED_RESEARCH_ONLY.
No local-PC execution.
No paid runner.
No b63 reliability scaling yet.
