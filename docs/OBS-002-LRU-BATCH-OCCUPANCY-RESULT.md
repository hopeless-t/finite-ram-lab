# OBS-002 — LRU batch occupancy result

> **Status:** COMPLETE / VALID DIAGNOSTIC WITH ONE INSTRUMENTATION CORRECTION
> **Run:** \`36617444105\`
> **Launch commit:** \`f480da31742595b83ce0d06b31f1ed43ec3a4de8\`
> **Kernel:** Ubuntu Azure \`7.0.0-1012-azure\`

## 1. Frozen diagnostic execution

- 4/4 hosted blocks: PASS
- 48/48 identities
- 24 measured touches/identity
- 1,152 measured touches
- no reliability scaling
- no natural-incidence claim
- no dynamic expansion

## 2. Instrumentation correction

The preregistered attempt to read \`folio_batch.nr\` at
\`__folio_batch_add_and_move()\` by dereferencing \`$arg1\` was invalid.

Reason:

\`$arg1\` is a \`struct folio_batch __percpu *\` base pointer.
The kernel function applies \`this_cpu_ptr(fbatch)\` before using it.

Observed impossible values above the 31-slot maximum confirmed the error.

This invalid field is not used in the corrected interpretation.

Valid observations remain:

- event count at \`__folio_batch_add_and_move\`;
- \`folio_batch_move_lru\` with an actual folio_batch pointer and valid \`nr\`;
- \`folios_put_refs\` with valid \`nr\`;
- \`page_counter_uncharge\`;
- user-space touch number and memory.current delta.

All **1,152/1,152 measured touches emitted exactly one LRU-add event**.

Therefore, for a trial whose first LRU flush is observed at measured touch T:

\`inferred initial occupancy = 31 - T\`

provided no earlier flush occurred.

The original frozen aggregate is preserved.
A corrected derived analysis is stored separately:

\`analysis/inputs/OBS-002-DERIVED-SUMMARY-v1.json\`

## 3. Negative events

Across 48 trials:

- exact -17: **11**
- other negative: one -1 event

Exact -17 touch distribution:

- touch 13: 2
- touch 14: 8
- touch 18: 1

All exact -17 touches had:

- one measured LRU-add event;
- successful +4 KiB process RSS growth;
- VmPTE delta 0.

## 4. Direct LRU-flush chain

Of 11 exact -17 events:

**9/11** showed the full same-touch chain:

\`\`\`
measured anonymous-page touch
-> LRU-add event
-> folio_batch_move_lru(nr=31)
-> folios_put_refs(nr=31)
-> page_counter_uncharge(..., 17)
\`\`\`

The other **2/11** exact -17 events had no observed worker LRU flush in the touch window:

- trial 1:1, touch 18, start 117 pages
- trial 3:4, touch 13, start 180 pages

LRU-flush and folios-put kprobes had **zero missed events in all four blocks**.

Therefore the absence of a worker LRU flush in these two specimens is real under the current probes.

page_counter_uncharge probes did have small global miss counts, so the uncharge caller for these two remains unresolved.

## 5. First-flush occupancy inference

A first worker LRU flush occurred within the 24-touch window in **26/48 trials**.

Because all 1,152 measured touches emitted exactly one LRU-add event, initial occupancy can be inferred from first-flush timing.

Observed inferred occupancies include:

- 7
- 9
- 12
- 14
- 15
- 17
- 18
- 19
- 20
- 25
- 26
- 27
- 30

### Occupancy 17 or 18

- n = **9**
- exact -17 at first flush = **9/9**

### All other observed occupancies

- n = **17**
- exact -17 at first flush = **0/17**

Exploratory one-sided Fisher exact:

\`p ~= 3.20e-7\`

This p-value is post-hoc and descriptive.
It is not a preregistered confirmatory test.

## 6. The 17 + 14 = 31 mechanism

Eight specimens infer:

- initial occupancy = 17
- 14 measured additions
- first flush at 31
- exact -17 uncharge

One specimen infers:

- initial occupancy = 18
- 13 measured additions
- first flush at 31
- exact -17 uncharge

The 18-entry specimen is compatible with:

- 18 entries present;
- 17 entries dead/releasable;
- one entry remaining live/non-released at flush.

The current leading mechanism is therefore:

1. the per-CPU LRU-add folio batch starts with a set of pre-existing entries;
2. a recurrent subset of **17** entries is dead/releasable but kept alive by batch references;
3. measured anonymous-page touches add one folio per touch;
4. when the 31-slot batch flushes, those dead/releasable references drop;
5. 17 folios are uncharged together;
6. memory.current emits -17 while the triggering anonymous page itself becomes resident.

This explains:

- the historical +17 start-state mode;
- touch-14 concentration;
- \`FOLIO_BATCH_SIZE = 31\`;
- \`page_counter_uncharge(17)\`;
- +4 KiB RSS on the same touch;
- VmPTE stability;
- lack of stock-phase shift.

## 7. What OBS-002 establishes

### Strongly supported

The dominant recurrent -17 phenomenon is an **LRU folio-batch release contaminant**, not a residual-stock consumption event.

A 31-slot LRU batch with approximately 17 releasable pre-existing entries explains 9 directly traced specimens and perfectly separates first-flush -17 behavior in the 26 traceable first-flush trials.

### Not yet closed

- two exact -17 specimens had no worker LRU flush;
- origin of the pre-existing/releasable folios;
- memcg/page-counter identity of those folios;
- whether the two non-LRU specimens are stock drain, another folio path, or another uncharge path.

## 8. Consequence for Q64 research

This result **strengthens**, rather than weakens, the Q64 stock model.

The recurrent -17 contamination is now mostly separated from:

- per-CPU memcg charge stock;
- Q64 batch arithmetic;
- PTE charge effects.

The controlled-spawn observer can eventually classify and exclude/report the LRU-release emission instead of treating every negative memory.current delta as a stock-state failure.

Do not retroactively rewrite frozen endpoints.

## 9. Evidence

Raw manifest:

- file count: **128**
- total bytes: **1,857,693**
- content-set SHA-256:
  \`c6ab5dbc6f218b4a992794e22df8baa6ef8ba5a8d219621ab2f1adcc1eb3abe8\`

GitHub Actions artifacts:

- block 0 SHA:
  \`5ccc12e6509e5189f5fee3262ee6636e880461825fff1b30142d757c20270af3\`
- block 1 SHA:
  \`834b177bf625c941e68eb0e93c0e0e2f9b6ce0f530b94b346f981bca828b6107\`
- block 2 SHA:
  \`8a7976c7aef79b34f9785bb3b82db0f31c07819898eb4077961a5507f91af33c\`
- block 3 SHA:
  \`a731bf33dde9b581b5bc27e7a87c0a0b6b70fe72fa11ead06b2e2a9790e0374b\`
- aggregate SHA:
  \`8195d5aa93a71002b4ea166106d592e993a0461256d5a76c28fdd5bec93c5dc3\`

Drive COLD locator:

\`Catfood Lab Evidence/finite-ram-lab/OBS-002-LRU-BATCH-OCCUPANCY-v1/run-36617444105\`

Drive restore verification:

\`5 / 5 BYTE-IDENTICAL PASS\`

## 10. Next discriminator

OBS-003 should be lower-overhead than OBS-002 and focus only on caller classification for the remaining non-LRU -17 population.

Suggested probes:

- system-wide \`page_counter_uncharge(nr_pages==17)\` + stacktrace;
- system-wide \`drain_stock\`;
- worker-only \`folio_batch_move_lru\`;
- worker-only \`folios_put_refs\`.

Primary classes:

- LRU_BATCH
- STOCK_DRAIN
- OTHER_STACK
- TRACE_MISS

The high-frequency \`__folio_batch_add_and_move\` probe is no longer required.
