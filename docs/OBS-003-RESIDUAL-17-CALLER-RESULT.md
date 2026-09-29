# OBS-003 — Residual -17 caller result and counter-identity correction

> **Status:** COMPLETE / FROZEN AGGREGATE + CORRECTED DERIVED INTERPRETATION
> **Run:** \`36620215583\`
> **Launch commit:** \`c0dfd89465eba54f9c435c6dd776e72d63cf4a48\`

## 1. Frozen aggregate

- 4/4 blocks PASS
- 48 trials
- 1,152 measured touches
- exact -17 events: 13

Frozen parser output:

- LRU_BATCH: 12
- OTHER_STACK: 1
- STOCK_DRAIN: 0

The frozen aggregate is preserved unchanged.

## 2. Corrected interpretation of the one OTHER_STACK specimen

The single OTHER_STACK specimen is:

- trial 3:1
- touch 23
- start memory.current: 115 pages
- observed delta: -17 pages

The coincident system-wide \`page_counter_uncharge(17)\` was executed by:

\`.NET Tiered Com\`

with stack:

\`shmem_fault -> shmem_alloc_and_add_folio -> folio_add_lru -> __folio_batch_add_and_move -> folio_batch_move_lru -> folios_put_refs -> page_counter_uncharge\`

This is not the worker command:

\`memcg005gc_spaw\`

The worker runs in a dedicated systemd service cgroup.

Therefore the external .NET event cannot be attributed to the worker's memory.current without proving that both events reference the same page_counter.

Corrected class:

\`UNRESOLVED_COUNTER_IDENTITY\`

not:

\`OTHER_STACK\`.

## 3. Strong direct result

12/13 exact -17 specimens have the complete worker-side chain:

\`worker LRU flush(31) -> worker folios_put(31) -> page_counter_uncharge(17)\`

and no drain_stock in the measured touch window.

For the unresolved specimen's block 3:

- drain_stock misses: 0
- LRU flush misses: 0
- folios_put misses: 0
- page_counter_uncharge misses: 0

Thus the absence of a worker LRU flush in that specimen is real under current probes.

What remains unknown is the identity of the page_counter responsible for the worker cgroup's -17 change.

## 4. Stock-drain finding

No exact -17 specimen is directly classified as STOCK_DRAIN in OBS-003.

A separate non-target observation exists:

- trial 2:7
- touch 1
- memory.current delta = -1
- a drain_stock event occurs in the same window
- the trace also shows refill/page-counter activity in kernel context

This demonstrates that stock/refill accounting activity is a real concurrent contaminant.

It does **not** prove that the drain caused the -1 delta because page-counter identity was not recorded.

## 5. Cross-run descriptive consistency

OBS-002:

- direct worker LRU-batch -17: 9/11

OBS-003:

- direct worker LRU-batch -17: 12/13

Combined descriptive count:

- direct worker LRU-batch: 21/24 exact -17 specimens

This is not a preregistered pooled estimator.

It supports the conclusion that LRU/folio-batch release is the dominant observed -17 mechanism on this hosted kernel.

## 6. Why counter identity is now the critical receipt

System-wide trace windows can contain unrelated processes.

Time coincidence alone is insufficient.

Future caller classification must require:

1. identify the worker memcg memory page_counter pointer from worker charge activity;
2. capture candidate uncharge counter pointer;
3. require pointer equality before assigning the uncharge to the worker cgroup.

This is stronger than matching:

- timestamp;
- CPU;
- comm;
- stack family.

## 7. Evidence

Raw manifest:

- 124 files
- 7,480,253 bytes
- content-set SHA-256:
  \`a0b5e7aa538778f5ac295e22b475ebf8fcfbe5f959f830af51b57f7cc2b4f67a\`

GitHub artifacts:

- block0: \`47878c2e53837656ae140422a25a394540b37141cd8fc4bebc4f076ed60aae4e\`
- block1: \`f5d99c4b04cc6a598c80c34fcf799a608481fa86a9d380d68b11b5982c458e27\`
- block2: \`44a68d2171389c5c5a8d2ec74ae7d7900f46355d2e9aeb8248892759b2668f14\`
- block3: \`549c147c34145303c4025335ad6829959b890f9411f6373e8961ec38629fdaae\`
- aggregate: \`c6899ea11bb590937d33fd542490bda19752ba0dc4303620b6538d4e0904d04f\`

Drive COLD:

\`Catfood Lab Evidence/finite-ram-lab/OBS-003-RESIDUAL-17-CALLER-v1/run-36620215583\`

Verification:

\`5 / 5 BYTE-IDENTICAL PASS\`

## 8. Next

OBS-004 — page-counter identity correlation.

Primary question:

Does every worker memory.current -17 have a matching \`page_counter_uncharge(17)\` on the same page_counter that the worker charged?

No b63 reliability scaling before this observer ambiguity is closed.
