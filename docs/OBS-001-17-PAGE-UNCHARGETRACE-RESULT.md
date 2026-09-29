# OBS-001 — 17-page uncharge trace result

> **Status:** COMPLETE / VALID DIAGNOSTIC
> **Run:** \`36615514509\`
> **Launch commit:** \`5338b2aaf51ca4e89bccdf60807894544a7fd7e5\`
> **Kernel:** Ubuntu Azure \`7.0.0-1012-azure\`
> **Question:** when \`memory.current\` emits exactly -17 pages, what kernel path performs the uncharge?

## 1. Frozen diagnostic execution

- 4/4 hosted blocks: PASS
- 48/48 identities executed
- 24 measured touches/identity
- 1,152 measured touches total
- no b63 reliability claim
- no natural-incidence claim
- no dynamic sample expansion
- no local-PC execution
- no paid runner

## 2. Observed negative events

Exact -17-page events:

- 5/1,152 measured touches

No other negative delta occurred in this diagnostic.

All five -17 specimens:

- started at 115 or 116 pages of \`memory.current\`;
- occurred at measured touch **14**;
- increased process VmRSS by **+4 KiB** on that touch;
- had **VmPTE delta = 0**;
- had no worker error.

## 3. Direct kernel trace

Every observed -17 touch had a coincident:

\`page_counter_uncharge(..., nr_pages=17)\`

The stack trace was the same in all five specimens:

\`\`\`
page_counter_uncharge
folios_put_refs
folio_batch_move_lru
__folio_batch_add_and_move
folio_add_lru
folio_add_lru_vma
do_anonymous_page
handle_pte_fault
__handle_mm_fault
handle_mm_fault
do_user_addr_fault
exc_page_fault
asm_exc_page_fault
\`\`\`

No \`drain_stock\` event was observed in any of the five -17 touch windows.

The frozen aggregate classifier therefore reported:

\`OTHER_UNCHARGE = 5\`

\`STOCK_DRAIN = 0\`

## 4. Probe-miss caveat

Kprobe profile:

### block 0

- drain_stock: 222 hits / 1 missed
- page_counter_uncharge: 4163 hits / 1 missed

block 0 contains three of the five -17 specimens.

Therefore absence of a coincident drain event in those three windows is strong evidence but not a mathematically perfect exclusion.

### block 3

- drain_stock: 200 hits / **0 missed**
- page_counter_uncharge: 4185 hits / **0 missed**

block 3 contains two -17 specimens.

Both have:

- page_counter_uncharge(17) with the LRU-folio stack above;
- no drain_stock event;
- zero relevant kprobe misses.

Therefore at least **2/2 miss-free direct specimens** establish that the -17 phenomenon can arise without \`drain_stock\`.

This falsifies the strong hypothesis:

> every -17 event is a preparation-CPU memcg stock drain.

## 5. The 17 + 14 = 31 clue

Fresh source audit against upstream Linux at:

\`6f8319e3e9a44dd537d17f41565a8453c560a581\`

shows:

- \`FOLIO_BATCH_SIZE = 31\`;
- \`folio_batch_add()\` fills the batch until zero slots remain;
- \`__folio_batch_add_and_move()\` calls \`folio_batch_move_lru()\` when the per-CPU batch fills;
- \`folio_batch_move_lru()\` finishes with \`folios_put(fbatch)\`;
- \`folios_put_refs()\` uncharges and frees folios whose final reference is dropped.

Observed:

- recurrent latent component: 17 pages;
- all valid diagnostic -17 emissions: touch 14.

And:

\`17 + 14 = 31\`

This creates a strong mechanistic hypothesis:

1. 17 charged folios are already represented in the relevant per-CPU LRU-add batch or otherwise held until that batch drains;
2. 14 measured anonymous-page additions fill the 31-slot batch;
3. the batch is flushed;
4. dropping batch references releases 17 dead/releasable folios;
5. their memcg charge is removed in one 17-page \`page_counter_uncharge\`.

This hypothesis explains simultaneously:

- the +17 start-state mode;
- the -17 emission;
- touch-14 timing;
- +4 KiB RSS on the triggering touch;
- no VmPTE growth;
- preservation of the measured stock phase in the previous controlled-spawn run.

## 6. What is proven vs not yet proven

### Directly established

- the -17 emission is associated with a 17-page page-counter uncharge;
- the observed uncharge occurs in the anonymous-fault LRU/folio-batch path;
- stock drain is **not required** for the -17 phenomenon;
- at least two miss-free specimens exclude drain_stock as the direct caller;
- the triggering touch itself successfully creates one new resident page.

### Strongly supported but not yet direct

- the 17 pages correspond to dead/releasable folios held until a 31-slot LRU-add batch flush;
- the 14th touch is the fill event because 17 pre-existing entries + 14 new entries = 31.

### Still unresolved

- the exact origin of the 17 pre-existing folios;
- whether all start-state +17 modes are the same LRU-batch phenomenon;
- whether the 17 folios belong to the current worker cgroup in every case or whether mixed-memcg per-CPU batch state contributes;
- the exact per-CPU LRU-batch occupancy immediately before measured touch 1.

## 7. Important correction to MATH-015 working hypothesis

Preparation-CPU memcg stock drain was a plausible candidate before OBS-001.

OBS-001 downgrades that explanation sharply.

The leading explanation is now:

\`deferred LRU-folio batch release / page-counter uncharge\`

rather than:

\`memcg stock drain\`.

This does **not** weaken the Q64 stock mechanism.

It removes an observer contaminant that had been incorrectly conflated with stock state.

## 8. Evidence

Raw manifest:

- files: 120
- total bytes: 13,731,781
- content-set SHA-256:
  \`aeee124d149aab0fb66023ff527e4982027b523290d864f5bc4e00a33a216335\`

Aggregate artifact:

- \`OBS-001-17-PAGE-UNCHARGETRACE-36615514509\`
- SHA-256:
  \`c977d4cfce13e65a795c5dba6af3335cf145e6c537d9a45db02b21ef9c8d505b\`

Drive COLD locator:

\`Catfood Lab Evidence/finite-ram-lab/OBS-001-17-PAGE-UNCHARGETRACE-v1/run-36615514509\`

Five archived ZIPs were re-downloaded from Drive.

Verification:

\`5 / 5 BYTE-IDENTICAL PASS\`

## 9. Next discriminator

The next diagnostic should directly observe LRU-batch occupancy.

Candidate OBS-002 probes:

- \`__folio_batch_add_and_move\`: batch \`nr\` before insertion;
- \`folio_batch_move_lru\`: batch \`nr\` at flush;
- \`page_counter_uncharge\`: 17-page event;
- \`page_counter_try_charge\` or equivalent counter identity if probeable.

Primary prediction:

For a -17 specimen at touch 14:

- batch occupancy before the touch should be 30;
- insertion should fill to 31;
- flush should occur immediately;
- page_counter_uncharge(17) should follow in that flush.

No reliability-scale b63 run should be launched before this contamination model is closed.
