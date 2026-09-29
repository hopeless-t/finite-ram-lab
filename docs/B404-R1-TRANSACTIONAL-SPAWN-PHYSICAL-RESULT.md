# B404 R1 — Transactional Spawn Physical Smoke Result

> **Run:** 36642120375  
> **Launch commit:** `0d2a3286f3e0346e101285c52670e0ab817e427c`  
> **Status:** PHYSICAL RUN COMPLETE / PROTOCOL SMOKE DID NOT PASS / OBSERVER v1 FALSIFIED  
> **No reliability claim.**

## Frozen R1 outcome

The physical runner executed all four blocks.

Normal lane:

- 12 scientific identities total;
- 10 ended `SUCCESS`;
- 0 ended `TARGET_FAIL`;
- 1 ended in instrumentation hold (`TRACE_GAP`);
- 1 ended `ABORTED` after exhausting its re-prime budget.

Sentinel lane:

- forced epoch-0 unexpected refill was detected;
- invalidated epoch 0 did not commit;
- hard re-prime opened epoch 1;
- epoch 1 acquired a fresh direct Q64;
- canonical target completed;
- **sentinel PASS**.

Frozen invalidation counts:

- `DRAIN_STOCK = 12`
- `TRACE_GAP = 1`
- `UNEXPECTED_REFILL = 1` — the intentional sentinel event.

Therefore:

`protocol_smoke_pass = false`.

Do not rewrite this historical result after the observer fix.

## Important negative result

`TARGET_FAIL = 0`.

R1 produced no complete uninterrupted verified epoch whose terminal stock pattern contradicted the b62/b63/b64 model.

That does **not** prove the model universally correct.

It means the physical smoke found observer-validity problems before it found a genuine target contradiction.

## Drain classifier v1 was too coarse

R1 treated every `drain_stock` event inside a marker window as a mutation of the target residual stock.

Raw trace forensics falsified that rule.

All normal workers used stock CPU 3.

Among the 12 R1 drain invalidations:

- **9/12 occurred on CPU 0**, typically in the Python controller;
- **3/12 occurred on CPU 3 during NORMALIZE touch 1**, in `memcg005gc_spaw`, inside the same direct-Q64 refill window;
- **0/12 were observed as same-stock-CPU post-verification drains**.

Linux memcg stock is per-CPU. Therefore a CPU-0 stock drain cannot directly clear the target residual stock cached on CPU 3.

The three same-CPU NORMALIZE cases match a second source-grounded path: `refill_stock()` can evict an existing slot with `drain_stock(stock, i)` before installing the newly verified memcg and its 63-page residual.

Prospective observer semantics are therefore changed to:

1. off-stock-CPU drain — record, do not invalidate target epoch;
2. same-stock-CPU drain during exact direct-Q64 NORMALIZE from the target worker — classify as normalization slot eviction, not destruction of the freshly established residual;
3. other same-stock-CPU drains — remain invalidating.

This is a correction to the observer, not a retroactive promotion of stopped R1 identities to success.

## TRACE_GAP was an attribution gap

One b62 identity stopped at:

- trial `0:0`;
- epoch 0;
- CONSUME touch 12.

The window contained:

- owner counter `0xffff8dc9c787b040`;
- `page_counter_uncharge(...,17)`;
- emitter `.NET TP Worker`;
- emitter CPU 2.

R1 had no stacktrace trigger on `page_counter_uncharge(17)`.

Because the matching LRU flush/put could fall outside the narrow PRE/POST window, the observer could not positively classify the owner uncharge as release-only and failed closed.

Prior OBS-001 directly established the characteristic stack:

`page_counter_uncharge -> folios_put_refs -> folio_batch_move_lru -> ...`

R2 therefore records the uncharge17 stack itself.

A release is positively classified when the owner-counter uncharge has the known LRU/folio stack, even if the batch-flush probe occurs just outside the marker window.

Unknown owner uncharges still fail closed.

## Postprocessing defect

The four block measurements and raw artifacts completed successfully.

Aggregate computation also completed and emitted the frozen summary above.

The workflow then failed in evidence-manifest generation:

`EvidenceResidencyError: files must be sorted by path`.

The bug was generic manifest ordering:

- filesystem `Path` traversal order was used before normalization;
- validation requires lexical normalized relative-path order.

The collector now explicitly sorts records by normalized `path`, with a regression test covering a sibling file/directory prefix such as:

- `trial-0-0.json`
- `trial-0-0/epoch-0.json`.

This postprocessing defect did not change the physical R1 measurements.

## Scientific interpretation

R1 is useful precisely because it did not produce a clean 12/12.

It demonstrated that B400-style fail-closed semantics work strongly enough to expose when the **observer itself is too conservative**.

The main result is:

> `drain_stock observed` is not sufficient to infer `target per-CPU residual stock destroyed`.

CPU locality and refill context are part of the receipt contract.

Likewise:

> `owner uncharge17 without same-window LRU events` is not sufficient to infer unknown mutation when a direct stack receipt can identify the known LRU release path.

## R2 change set

R2 changes only observer/evidence plumbing:

- CPU-aware drain attribution;
- NORMALIZE slot-eviction distinction;
- uncharge17 stack-grounded release classification;
- normalized evidence-manifest path ordering.

The stock arithmetic, target arms, re-prime budget, sample count, and sentinel semantics remain unchanged.

## Historical integrity

R1 remains:

- 10/12 normal SUCCESS;
- 1 instrumentation HOLD;
- 1 ABORTED;
- 0 TARGET_FAIL;
- sentinel PASS;
- overall protocol smoke FAIL under observer v1.

R2 is a new physical experiment generation and must be reported separately.
