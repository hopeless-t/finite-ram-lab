# CURRENT

> Latest bounce: B394
> Stage: DOMINANT -17 MECHANISM = LRU/FOLIO-BATCH RELEASE
> Stop: READY FOR OBS-003 RESIDUAL-CALLER DISCRIMINATOR

## OBS-001

Established:
- page_counter_uncharge(17)
- stack through anonymous-fault LRU/folio path
- stock drain not required for -17

## OBS-002

Run:
\`36617444105 = success\`

Scale:
- 48 trials
- 1152 touches

Exact -17:
11

Full LRU-flush chain:
9/11

Chain:
\`LRU add -> flush31 -> folios_put31 -> page_counter_uncharge17\`

Two unresolved:
- trial 1:1 touch18 start117
- trial 3:4 touch13 start180

LRU flush / folios_put probe misses:
0 across all blocks.

## Corrected occupancy analysis

The direct pre-insert nr field was invalid:
\`__folio_batch_add_and_move\` arg1 is a __percpu base pointer.

Do not use the frozen aggregate's empty histograms as evidence.

Corrected derived summary:
\`analysis/inputs/OBS-002-DERIVED-SUMMARY-v1.json\`

All 1152 touches:
exactly one LRU-add event.

Therefore for a first flush at touch T:
\`inferred initial occupancy = 31 - T\`

First flush observed:
26/48 trials.

Occupancy17/18:
- 9 trials
- 9/9 exact -17 at first flush

Other occupancy:
- 17 trials
- 0/17 exact -17 at first flush

Exploratory Fisher:
~3.20e-7

## Leading mechanism

FOLIO_BATCH_SIZE =31.

Dominant phenotype:
17 pre-existing releasable entries +14 additions -> flush31 -> uncharge17.

One 18-entry case is compatible with:
17 releasable +1 surviving entry.

## Evidence

Raw:
- 128 files
- 1,857,693 bytes
- SHA:
  \`c6ab5dbc6f218b4a992794e22df8baa6ef8ba5a8d219621ab2f1adcc1eb3abe8\`

Drive:
\`Catfood Lab Evidence/finite-ram-lab/OBS-002-LRU-BATCH-OCCUPANCY-v1/run-36617444105\`

Verification:
5/5 BYTE-IDENTICAL PASS

## Next

OBS-003 residual-caller discriminator.

Question:
what causes the exact -17 specimens without a worker LRU flush?

Trace:
- page_counter_uncharge17 + stacktrace
- drain_stock
- worker LRU flush
- worker folios_put

No high-frequency lru_add probe.

## Authority

HOSTED_RESEARCH_ONLY.
No local-PC execution.
No paid runner.
No b63 reliability scaling yet.
