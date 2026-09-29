# RETROSPECTIVE — Transactional reclassification of historical Q64 evidence v1

> Status: HISTORICAL REPLAY / NO NEW PHYSICAL RUN
> Validator: B400 TRANSACTIONAL-REPRIME-v1
> Frozen-result policy: original endpoints and labels remain immutable.

## 1. Question

Reclassify the lab's earlier SUCCESS / FAIL observations using the higher-resolution transactional semantics introduced at B400.

The goal is not to rescue failed trials or rewrite preregistered endpoints.

The goal is to distinguish:

- target mechanism failure;
- inability to acquire a verified reset;
- loss of a previously verified state;
- observer contamination;
- missing receipts in legacy runs;
- pre-transaction initial-state variation.

## 2. New replay classes

### TX_SUCCESS

A complete verified epoch:

1. direct page_counter_try_charge(64);
2. direct refill_stock(63);
3. VmPTE clean;
4. CPU match;
5. trace complete;
6. no later invalidator;
7. target match;
8. COMMIT.

### TX_TARGET_FAIL

A genuine target mismatch after a verified uninterrupted epoch.

This is scientific failure and is not retried away.

### TX_NO_RESULT_INVALIDATED

An invalidator occurs:

- unexpected refill;
- drain_stock;
- PTE growth;
- CPU mismatch;
- worker error;
- trace gap.

The attempt yields no target conclusion.

### TX_NO_RESULT_RECEIPT_GAP

The historical run predates the receipts needed to open VERIFIED.

Fail closed.

This is not the same as TARGET_FAIL.

### TX_NONTERMINAL_VERIFIED

A verified reset is directly observed, but the evidence object has no target/commit phase.

### TX_PRETRANSACTION

Admission-gate or natural initial-state evidence.

These observations are not target successes or failures.

### TX_OBSERVER_SUPPORT

Evidence that establishes how a raw emission should be interpreted by the transaction observer.

## 3. MEMCG-005F — 98.374% was an admission metric

Frozen historical result:

- REMOTE_LOW n = 123
- first-touch Q64 = 121/123
- first-touch zero = 2/123

Replay:

- 121 = TX_PRETRANSACTION / predictor hit
- 2 = TX_PRETRANSACTION / normalization needed
- 0 = TX_TARGET_FAIL

The old 1.626% tail is not evidence that the post-reset target transition failed.

REMOTE_LOW predicted favorable initial phase; it did not prove verified state.

## 4. MEMCG-005G-A — all 28 old first-touch failures recovered

Frozen historical result:

- 406 valid REMOTE_LOW
- 28 first-touch zero
- 28/28 reached a later Q64 by touch65

Replay:

- all 28 = TX_PRETRANSACTION / recovery observed
- 0 = TX_TARGET_FAIL

This is the clearest historical demonstration that first-touch zero and target-mechanism failure are different events.

The depth1/deep-tail phenotype remains scientifically useful, but it describes hidden initial phase.

## 5. MEMCG-004 — strong mechanism support, insufficient B400 receipts

Frozen historical result:

- 4/4 calibrated blocks found a net +64 reset candidate
- 4/4 reproduced 63 zero-delta consuming touches followed by the next +64
- CPU-ready receipts were clean

Replay:

- 4/4 = strong legacy reset/phase support
- 4/4 = TX_NO_RESULT_RECEIPT_GAP if forced through B400
- 0 = TX_TARGET_FAIL

Reason:

MEMCG-004 predates the direct charge-side token.

It observed net memory.current, not the required paired:

page_counter_try_charge(64) + refill_stock(63).

The scientific result survives; the certification level changes.

## 6. Controlled-spawn v2 — the largest reclassification

Frozen endpoint:

- n = 72
- strict exact recovery = 49/72
- primer found = 55/72
- primer-qualified terminal pattern = 55/55
- calibration OTHER = 17
- BAIT_NONZERO = 6

The 49/72 endpoint remains frozen.

The 55/55 conditional mechanism result remains frozen.

### 6.1 Old strict successes: 49

These trials had:

- a net +64 primer;
- zero measured VmPTE growth;
- CPU/worker integrity;
- expected terminal pattern.

However the run did not record the new direct charge64 + refill63 receipt pair.

Therefore:

- legacy interpretation: strict success
- B400 replay: TX_NO_RESULT_RECEIPT_GAP
- retroactive TX_SUCCESS: 0

This is intentionally conservative.

Higher-resolution validation can downgrade certification without invalidating the old experimental result.

### 6.2 Six BAIT_NONZERO failures

Frozen bait deltas:

- -17
- -17
- -17
- -13
- -3
- -2

All six nevertheless produced the exact predicted terminal phase.

The later observer program showed that negative memory.current emissions are not equivalent to stock consumption.

For the recurrent -17 lane, OBS-005 directly established a cross-cgroup LRU release mechanism.

But B400 permits RELEASE_ONLY only when the emission is positively classified by observer receipts.

The controlled-spawn run did not record those source-grounded receipts.

Therefore all six remain:

TX_NO_RESULT_RECEIPT_GAP

not TX_TARGET_FAIL.

The three -17 cases are strong release-compatible historical specimens.

The -13/-3/-2 cases remain unknown negative emissions and fail closed.

None may be retroactively promoted to TX_SUCCESS.

### 6.3 Seventeen calibration OTHER failures

The controlled-spawn retrospective records the calibration failures as the recurrent -17 lane.

The old runner stopped before acquiring a primer.

Under the new protocol a positively classified release-only emission would not terminate normalization; normalization would continue until a direct Q64 token is acquired or the bounded budget is exhausted.

Historical replay cannot prove which of the 17 would later have normalized because the required charge-side trace is absent.

Therefore:

- 17 = TX_NO_RESULT_RECEIPT_GAP / normalization terminated early
- 0 = TX_TARGET_FAIL

### 6.4 Controlled-spawn headline

Among the 72 frozen identities:

- historical strict success remains 49
- historical strict failure remains 23
- historical primer-qualified target match remains 55/55
- valid verified-epoch target mismatch observed = 0
- B400 accepted TX_SUCCESS = 0

The final line does not mean the mechanism regressed from 49 successes to zero.

It means no historical target run contains the complete receipt chain required by the new certification boundary.

This is a certification gap, not a measured performance collapse.

## 7. OBS-005 — release classifier evidence

Frozen OBS-005:

- 16 total
- 15 scrub-success
- all 15/15 scrub-success trials showed producer memory.current -17
- 12/12 counter-grounded cases directly showed producer page-counter uncharge17
- 3 counter-unknown due overwritten trace
- 1 scrub-no-flush

Replay role:

- 12 = TX_OBSERVER_SUPPORT / release-only grounded
- 3 = receipt gap if used transactionally
- 1 = precondition/setup failure

OBS-005 is not a target transaction.

Its importance is that it supplies the source-grounded interpretation needed to avoid treating release emissions as stock consumption.

## 8. OBS-006 — first evidence that genuinely reaches VERIFIED

Corrected frozen result:

- 16 trials
- MASKED_Q64_PASS = 14
- STOCK_STATE_LOST = 2

All 14 passes directly recorded:

- page_counter_try_charge(...,64)
- refill_stock(...,63)
- LRU flush / folios_put
- same-counter page_counter_uncharge(...,17)
- net memory.current = +47

Replay:

- 14 = TX_NONTERMINAL_VERIFIED
- 2 = TX_NO_RESULT_INVALIDATED / unexpected refill
- 0 = TX_TARGET_FAIL

This is the first historical evidence set that satisfies the new direct reset token.

It does not become TX_SUCCESS because OBS-006 was an observer experiment, not a target+commit experiment.

The two rejected trials demonstrate the new abstention semantics correctly:

state loss is NO_RESULT, not false target failure.

## 9. G0 PTE-growth specimens — visible Q64 is no longer enough

Historical G0 LOW PTE-growth subset:

- 5 specimens
- 5/5 net Q64
- 0/5 exact-zero

Under the old coarse observer these look favorable.

Under B400:

PTE_GROWTH has precedence over a positive Q64 interpretation.

Replay:

- 5/5 = TX_NO_RESULT_INVALIDATED / PTE_GROWTH

This is a concrete example where the new classifier intentionally rejects an apparently successful old observation.

## 10. G-B / G-F / G0 natural exact-zero cohorts

The natural first-touch panels remain valid measurements of initial-state incidence and environmental dependence.

They are not target transactions.

Examples:

- G-B CAP8: 3/240 exact-zero
- G-B CAP70: 26/249 exact-zero
- G-F LOW: 91/1,374 exact-zero
- G0 LOW: 19/496 exact-zero

Replay class:

TX_PRETRANSACTION

These observations belong to the predictor / hidden-state model, not the TARGET_FAIL denominator.

## 11. Pseudo-council replay audit

### Experimentalist

Preserve all preregistered historical endpoints.

Do not convert 49/72 to 55/72.

### Protocol engineer

Fail closed when the direct reset token is absent.

Do not infer charge/refill receipts from net memory.current.

### Observer specialist

A negative net delta may coexist with a valid charge transition.

Only positively classified release emissions receive state-preserving treatment.

### Statistician

Do not pool:

- admission hit rate;
- normalization burden;
- accepted-result correctness;
- target-failure rate;
- abstention rate.

### Council convergence

4/4 positions converge on the same rule:

historical labels remain frozen, while the new validator adds a second, stricter transactional classification.

## 12. What changed scientifically

Old binary view:

SUCCESS vs FAIL

New view:

1. predictor hit/miss;
2. normalize;
3. verified reset;
4. execute;
5. state invalidation / abstain;
6. target match/mismatch;
7. commit.

This changes the interpretation of the historical failure population.

The strongest current conclusion is:

there is not yet historical evidence of a genuine target mismatch occurring after a B400-complete verified epoch.

That is not proof that the true TARGET_FAIL probability is zero.

It means earlier experiments did not isolate that estimand.

## 13. What changed on the success side

The new classifier is stricter in both directions.

It rescues false failures from being called target failures, but it also refuses to certify old successes whose receipt chain is incomplete.

Therefore the replay produces the apparently paradoxical result:

- fewer historical accepted successes;
- fewer historical scientific failures;
- more NO_RESULT / PRETRANSACTION classes;
- much cleaner meaning for any future SUCCESS.

This is the desired behavior.

## 14. Next experiment-design consequence

Do not run a large reliability panel yet.

The next physical target experiment should make every trial natively emit B400 packets:

- NORMALIZE packets with direct charge/refill receipts;
- explicit release-only classification;
- PTE/CPU/worker/trace guards;
- CONSUME packets;
- TARGET packet;
- COMMIT;
- bounded REPRIME.

Then the lab can estimate separately:

- accepted-result correctness;
- genuine TARGET_FAIL rate;
- re-prime burden;
- normalization depth;
- abort/abstention rate.

## 15. Frozen machine-readable replay

See:

analysis/inputs/HISTORICAL-TRANSACTION-REPLAY-v1.json

No physical execution was performed in this replay.
