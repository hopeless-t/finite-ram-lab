# B393 — OBS-001 identifies the -17 caller family

## Status

OBS-001 COMPLETE / RESULT FROZEN / EVIDENCE COLD-VERIFIED.

Run:
\`36615514509\`

## Direct result

48 trials / 1,152 measured touches.

Exact -17 events:
5

All five:
- start at 115 or 116 pages
- occur at touch 14
- VmRSS +4 KiB
- VmPTE delta 0
- worker error 0
- coincident page_counter_uncharge(..., 17)

Observed stack in all five:

page_counter_uncharge
-> folios_put_refs
-> folio_batch_move_lru
-> __folio_batch_add_and_move
-> folio_add_lru
-> folio_add_lru_vma
-> do_anonymous_page

No drain_stock event was observed in those windows.

Aggregate class:
OTHER_UNCHARGE = 5

## Miss caveat

block 0 has one global missed hit on drain_stock and page_counter probes.
It contains 3/5 specimens.

block 3 has:
- drain_stock misses = 0
- page_counter_uncharge misses = 0

and contains 2/5 specimens.

Therefore at least two direct miss-free specimens establish that stock drain is not required for -17.

## New leading mechanism

Linux source:
FOLIO_BATCH_SIZE = 31.

All valid -17 emissions:
touch 14.

Observed latent component:
17 pages.

17 + 14 = 31.

Leading hypothesis:

17 dead/releasable folios are held until a per-CPU LRU-add folio batch fills;
touch 14 fills the 31-slot batch;
batch flush drops references;
17 folios are uncharged together.

This explains:
- +17 start mode
- -17 emission
- touch-14 timing
- successful +1 RSS touch
- no PTE growth
- no stock-phase shift

Not yet directly established:
- initial LRU-batch occupancy
- origin/cgroup identity of the 17 folios

## Evidence

Raw manifest:
- 120 files
- 13,731,781 bytes
- content-set SHA:
  aeee124d149aab0fb66023ff527e4982027b523290d864f5bc4e00a33a216335

Drive COLD:
Catfood Lab Evidence/finite-ram-lab/OBS-001-17-PAGE-UNCHARGETRACE-v1/run-36615514509

5/5 archive ZIPs:
BYTE-IDENTICAL PASS

## Next

OBS-002:
directly trace LRU-batch occupancy and counter identity.

Primary prediction:
- pre-touch14 batch occupancy = 30
- insertion fills batch to 31
- immediate flush
- page_counter_uncharge(17)

No b63 reliability scaling yet.
