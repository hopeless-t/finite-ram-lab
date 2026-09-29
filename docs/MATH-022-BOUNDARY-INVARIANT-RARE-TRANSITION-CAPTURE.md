# MATH-022 — Boundary Invariant and Rare-Transition Capture

> Status: DESIGN MATH / NO PHYSICAL RUN  
> Chapter: finite-ram-lab II  
> Goal: turn a verified Q64 epoch into a deterministic boundary test and use any unexplained phase shift as a rare-transition specimen.

## 1. Canonical invariant

Immediately after a verified direct Q64 event:

- one data page has been satisfied from a newly charged 64-page batch;
- refill_stock records 63 residual pages.

Define:

- R_0 = 63, residual stock immediately after the verified primer;
- t = post-primer measured data-page touch index.

Under the clean model, while R is nonzero:

R_t = R_(t-1) - 1.

Therefore by induction:

R_t = 63 - t

for t = 0..63.

So:

- post-primer touches 1..63 consume stock without a new charge batch;
- after touch 63, residual becomes zero;
- post-primer touch 64 must acquire the next direct Q64 batch.

Canonical boundary:

T_0 = 64.

This is conditional on:

- the same intended memcg/CPU stock lane;
- one fresh measured data page per touch;
- no PTE growth;
- no drain_stock;
- no unexpected refill/reset;
- complete observer receipts;
- no CPU/worker error.

A positively classified LRU release does not appear in the recurrence because it changes accounting visibility, not residual stock.

## 2. Boundary innovation

Let T be the first post-primer direct Q64 touch in a complete uninterrupted epoch.

Define:

Delta = T - 64.

Then:

- Delta = 0: canonical boundary;
- Delta < 0: stock exhausted early;
- Delta > 0: stock lasted longer than the canonical model.

If an unobserved mechanism changes residual stock by an integer net amount U before the boundary, with positive U adding effective residual and negative U consuming residual, then under the same simplified single-batch model:

T = 64 + U

and therefore:

U = Delta.

This turns phase shift into a quantitative fingerprint.

Examples:

- T = 63 -> Delta = -1 -> one-page-equivalent unexplained residual loss;
- T = 62 -> Delta = -2 -> two-page-equivalent loss;
- T = 65 -> Delta = +1 -> one-page-equivalent residual addition or missed accounting/observer event.

The mapping is a localization tool, not an automatic causal label.

## 3. Why b62/b63/b64 form a local barcode

The existing terminal patterns are:

- b62: ZERO, ZERO, Q64
- b63: ZERO, Q64
- b64: Q64

They are a local finite-difference probe around the expected boundary.

A one-page early shift changes the barcode in a directional way:

- b63 tends to expose Q64 one touch early;
- b62 shortens from ZERO,ZERO,Q64 to ZERO,Q64 at the shifted boundary.

A one-page late shift makes b64 begin with ZERO rather than Q64.

Thus the three arms identify the sign of a local phase displacement without relying on net memory.current.

## 4. The rare-pokemon specimen

The Chapter-II target is not merely an unexpected Q64.

An early or late boundary is the symptom.

The rare specimen is:

UNEXPLAINED_BOUNDARY_DEVIATION

defined by:

- verified direct Q64 start;
- complete epoch-local receipts;
- CPU match;
- worker clean;
- no PTE growth;
- no observed drain;
- no known state-changing antecedent;
- all owner release events positively classified or absent;
- T != 64.

If this occurs, freeze the specimen.

Do not re-prime the same scientific identity and continue as though nothing happened.

The epoch becomes evidence.

## 5. Capture protocol

For a candidate:

1. stop before COMMIT;
2. freeze the complete epoch packet archive;
3. freeze owner_counter;
4. retain at least the last 8 pre-boundary trace windows and 2 post-boundary diagnostic windows if protocol-safe;
5. retain direct charge/refill/drain/LRU/PTE/CPU receipts;
6. classify the observed innovation Delta;
7. open a new independent identity for reproduction.

The original specimen remains immutable.

## 6. Touch age versus wall-clock age

Chapter II records both:

a = touch_index_since_verified

and:

tau = elapsed_ns_since_verified.

This permits a critical discrimination.

### Touch-driven mechanism

If deviation probability tracks a while remaining stable across different tau:

candidate causes are transitions driven by page activity / stock consumption.

### Time-driven mechanism

If deviation probability rises with tau at fixed or similar a:

candidate causes are asynchronous activity:

- workqueue action;
- external CPU-local competition;
- reclaim/control activity;
- delayed maintenance.

Current Linux memcg code contains a cross-CPU drain path where drain_all_stock can queue per-CPU drain work on the memcg workqueue.

Therefore wall-clock exposure is a mechanistically meaningful axis, not merely timing noise.

## 7. Competing-risk model

Do not collapse every terminated epoch into failure.

For each verified epoch, record the first event among:

- canonical boundary;
- unexpected refill;
- drain;
- PTE growth;
- CPU mismatch;
- worker error;
- trace gap;
- unexplained boundary deviation.

Known invalidators are competing causes.

The unknown-mechanism hunt should estimate a residual cause-specific hazard rather than:

P(failure per touch).

A useful discrete model is:

h_j(a, tau) =
P(cause j occurs at next observation |
  epoch valid through current observation).

The rare target is h_U for the unexplained cause U.

## 8. What can be mathematically proved

### Protocol theorem

From the reducer/archive implementation, properties such as these can be exhaustively tested/model-checked:

- no COMMIT from an invalidated epoch;
- stale epoch receipts cannot authorize a new epoch;
- release-only does not decrement residual;
- TARGET_MISMATCH is not retried away;
- re-prime requires fresh verification.

These are software/protocol properties.

### Boundary theorem

Given the clean-model assumptions, T_0 = 64 follows by induction from R_0 = 63 and one-page consumption.

This is a conditional mechanistic theorem.

### What cannot be proved from math alone

Mathematics cannot prove that the physical observer has no blind spot.

If T != 64 with no known antecedent, the alternatives still include:

- a genuinely unknown stock-changing mechanism;
- an observer false negative;
- a violated modeling assumption;
- instrumentation loss not detected by current completeness checks.

The experiment and sentinels are required to separate these.

## 9. Statistical absence bound

Suppose n independent accepted clean epochs show zero unexplained deviations.

A one-sided 95% upper bound for per-epoch unexplained-deviation probability p is:

p_upper = 1 - 0.05^(1/n).

For large n this is approximately:

3/n.

This bounds rarity; it does not prove p = 0.

Correlated runner/block behavior must be handled separately rather than pretending every touch is independent.

The epoch/identity should be the primary sampling unit.

## 10. Strongest discovery condition

The most valuable observation is:

- complete receipt chain;
- all known invalidators absent;
- owner release fully explained;
- boundary shift reproducible in independent identities;
- shift magnitude and timing cluster.

At that point the search can move from:

"does an unknown transition exist?"

to:

"which kernel path generates a Delta of this magnitude at this age?"

That is the intended Chapter-II discovery loop.

## 11. Research decision

First prove the observer with B404/B405.

Then hunt boundary innovations.

Do not scale reliability certification before the unexplained-boundary channel is either empty within a declared bound or mechanistically classified.
