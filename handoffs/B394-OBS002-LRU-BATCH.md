# B394 — OBS-002 isolates dominant LRU-batch -17 mechanism

## Status

OBS-002 COMPLETE / DERIVED ANALYSIS CORRECTED / EVIDENCE COLD-VERIFIED.

Run:
\`36617444105\`

## Direct observations

48 trials / 1,152 measured touches.

Exact -17:
11

Full same-touch chain:

\`LRU add -> folio_batch_move_lru(nr=31) -> folios_put_refs(nr=31) -> page_counter_uncharge(17)\`

Observed:
9/11 exact -17 specimens.

Two exact -17 specimens had no observed worker LRU flush:
- 1:1 touch18 start117
- 3:4 touch13 start180

LRU-flush and folios-put probes:
0 misses across all blocks.

Therefore the two unresolved specimens are a real residual class under current instrumentation.

## Instrumentation correction

Direct \`nr\` read at \`__folio_batch_add_and_move\` was invalid because arg1 is a \`__percpu\` base pointer.

Frozen aggregate remains unchanged.

Corrected derived analysis:
\`analysis/inputs/OBS-002-DERIVED-SUMMARY-v1.json\`

Valid facts:
- all 1,152 measured touches generated exactly one LRU-add event
- first valid LRU flush has nr=31

Thus:
\`initial occupancy = 31 - first_flush_touch\`

for trials with a first flush inside the 24-touch window.

## Occupancy result

26/48 trials had first LRU flush within 24 touches.

Inferred initial occupancy 17 or18:
- n=9
- -17 at first flush: 9/9

All other observed occupancies:
- n=17
- -17 at first flush: 0/17

Exploratory one-sided Fisher:
~3.20e-7

Post-hoc descriptive, not confirmatory.

## Mechanism

Dominant model:

- LRU-add batch capacity =31
- recurrently ~17 pre-existing entries are dead/releasable
- 14 measured additions commonly fill the batch
- flush drops batch refs
- 17 pages are uncharged together

Eight direct examples:
17 + 14 =31 -> -17

One direct example:
18 +13 =31 -> -17
compatible with 17 releasable +1 live entry.

## Meaning for Q64

The dominant -17 contamination is not residual-stock consumption.

It is an LRU/folio release emission.

This removes a major observer contaminant from the Q64 stock model.

Frozen historical endpoints remain unchanged.

## Evidence

Raw:
- 128 files
- 1,857,693 bytes
- content-set SHA:
  \`c6ab5dbc6f218b4a992794e22df8baa6ef8ba5a8d219621ab2f1adcc1eb3abe8\`

Drive:
\`Catfood Lab Evidence/finite-ram-lab/OBS-002-LRU-BATCH-OCCUPANCY-v1/run-36617444105\`

5/5 archive ZIPs:
BYTE-IDENTICAL PASS

## Next

OBS-003:
classify the residual 2/11 non-LRU -17 population.

Use lower-overhead tracing:
- system-wide page_counter_uncharge(17) + stacktrace
- system-wide drain_stock
- worker-only folio_batch_move_lru
- worker-only folios_put_refs

Classes:
- LRU_BATCH
- STOCK_DRAIN
- OTHER_STACK
- TRACE_MISS

Do not restore the high-frequency lru_add probe.

No b63 reliability scaling yet.
