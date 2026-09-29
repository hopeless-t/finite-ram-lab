# CURRENT

> Latest bounce: B393
> Stage: -17 CALLER IDENTIFIED AS LRU/FOLIO-BATCH UNCHARGE FAMILY
> Stop: READY FOR OBS-002 LRU-BATCH-OCCUPANCY DISCRIMINATOR

## OBS-001

Run:
36615514509 = success

Scale:
- 4 blocks
- 48 trials
- 1152 touches

Exact -17:
5

All five:
- start 115/116 pages
- touch 14
- VmRSS +4 KiB
- VmPTE delta 0
- page_counter_uncharge(17)
- stack through folios_put_refs / folio_batch_move_lru / __folio_batch_add_and_move / folio_add_lru / do_anonymous_page

No observed drain_stock in those windows.

Miss-free block 3 contributes 2/2 direct specimens with:
- drain_stock misses 0
- page_counter_uncharge misses 0

Therefore:
Prep-CPU stock drain is not required for -17.

## Leading mechanism

Linux:
FOLIO_BATCH_SIZE = 31

Observation:
17 latent pages + touch 14 = 31

Hypothesis:
17 dead/releasable folios are held until LRU-add batch fill;
touch 14 fills the batch;
flush drops refs;
17 pages uncharge.

Not yet directly proven:
- pre-touch occupancy
- origin/cgroup identity of the 17 folios

## Evidence

Doc:
docs/OBS-001-17-PAGE-UNCHARGETRACE-RESULT.md

Raw:
- files 120
- bytes 13,731,781
- content-set SHA:
  aeee124d149aab0fb66023ff527e4982027b523290d864f5bc4e00a33a216335

Drive:
Catfood Lab Evidence/finite-ram-lab/OBS-001-17-PAGE-UNCHARGETRACE-v1/run-36615514509

Verification:
5/5 BYTE-IDENTICAL PASS

## Next

OBS-002:
trace LRU-batch occupancy and page-counter identity.

Primary prediction:
pre-touch14 occupancy 30 -> fill 31 -> flush -> uncharge17.

## Authority

HOSTED_RESEARCH_ONLY.
No local-PC execution.
No paid runner.
No b63 reliability scaling yet.
