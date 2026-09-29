# MATH-017 — Success-side reframe: from 98.4% admission to verified transaction

> Status: RETROSPECTIVE MODEL / NO NEW PHYSICAL RUN
> Inputs: MEMCG-004, MEMCG-005F, MEMCG-005G-A/B, controlled-spawn v2, OBS-001..006.

## 1. Original 1.6%

MEMCG-005F REMOTE_LOW:

- first-touch Q64: 121/123 = 98.374%
- first-touch zero: 2/123 = 1.626%

At that time the operational objective naturally looked like:

P(first touch is Q64 | REMOTE_LOW) -> 1

The later evidence shows this is no longer the best correctness target.

## 2. REMOTE_LOW was a predictor, not the state

REMOTE_LOW combined:

- startup on P
- measurement on remote S
- pre_current <= 110

It predicted fresh first-touch Q64 extremely well.

But later capacity experiments showed the failure probability changes with footprint regime.

CAP8 remains near the old tail:
- MEMCG-005F: 1.626%
- G-B CAP8: 1.25%

Larger footprint arms can raise natural exact-zero incidence substantially.

Therefore the old 1.6% is not a universal irreducible mechanism error.

It is a conditional initial-state probability under one regime.

## 3. First-touch zero is often delayed success

G-A biopsied 28 first-touch zero specimens.

All 28/28 reached a later Q64 by touch65.

This is crucial.

A first-touch zero does not imply that the Q64 mechanism failed.
It means the target CPU started from an unknown nonempty residual phase.

MEMCG-004 independently showed the correct strategy:

- do not assume startup phase;
- keep touching until a fresh Q64 is actually observed;
- after that observed reset, 63 stock-consuming touches and the next Q64 were exact in 4/4 blocks.

Thus state acquisition is stronger than state prediction.

## 4. Post-primer success is a different population

Controlled-spawn v2:

- 72 frozen raw identities
- 55 direct Q64 primers
- 55/55 primer-qualified terminal phase matches

The frozen strict endpoint remains 49/72.

The correct interpretation is not that 23 trials prove the transition mechanism fails.

The strict failures combine:
- primer acquisition / early stopping;
- observation contamination;
- state validity;
- post-primer execution.

Once a valid Q64 reset was observed, the one-page phase arithmetic matched 55/55.

## 5. The -17 lane changed the meaning of failure

The recurrent -17 event is now strongly identified as deferred LRU release.

It is not residual-stock consumption.

Therefore a negative net memory.current observation cannot be used to declare stock-state failure by itself.

A touch can simultaneously:
- consume/refill stock;
- release unrelated/deferred folios.

The observer must separate those emissions.

## 6. OBS-006 changed the success token

OBS-006 deliberately constructed:

+64 Q64 charge
-17 LRU release
= +47 net memory.current

Corrected run:

- MASKED_Q64_PASS 14/16
- STOCK_STATE_LOST 2/16

In all 14 state-preserved trials, the direct charge observer recognized Q64 despite net +47.

Therefore:

OLD SUCCESS TOKEN:
memory.current delta == +64

NEW SUCCESS TOKEN:
direct page_counter_try_charge(64)
AND direct refill_stock(63)
AND PTE-clean receipt
AND no unexpected state-invalidating transition

Net memory.current is secondary.

## 7. The two remaining OBS-006 failures are informative

They were not observer failures.

They were explicit state losses:

- one unexpected refill at PRODUCER touch1;
- one unexpected refill at CONSUME touch20 and again at PRODUCER touch1.

The observer correctly rejected them.

This means the bottleneck moved again:

from
"Can we identify Q64?"

to
"Can we preserve or re-acquire a verified stock state when asynchronous CPU-local activity perturbs it?"

## 8. Revised success architecture

A static gate should no longer be the correctness boundary.

Use a closed-loop transaction.

### Phase A — cheap admission

REMOTE_LOW / low-footprint conditions can remain a fast-path predictor.

They reduce expected normalization work.

They are not proof of state.

### Phase B — normalize

- precondition target PTE table;
- migrate to target stock CPU;
- touch fresh data pages;
- directly observe charge-side events;
- ignore/classify LRU release emissions separately;
- continue until a verified Q64 reset is observed.

Under a stable stock process, the next refill should be reachable within one batch cycle rather than requiring lucky first-touch phase.

### Phase C — open a verified critical state

After direct Q64:

R = 63

Maintain an expected residual counter.

Continuously monitor:
- unexpected refill_stock;
- drain_stock;
- CPU mismatch;
- VmPTE growth;
- other state-invalidating receipts.

Any such event invalidates the transaction.

Do not call it target failure.

Re-prime.

### Phase D — execute target transition

Consume the frozen number of pages and evaluate b62/b63/b64 or successor construction.

### Phase E — commit only with complete receipts

Only publish SUCCESS when:
- reset was directly observed;
- state remained valid;
- target transition matched;
- observer receipts are complete.

Otherwise:
INVALIDATE / RE-PRIME.

## 9. What '100%' can mean

Finite experiments cannot prove a literal universal probability of 1.

Three different targets must be separated.

### 9.1 First-attempt completion

P(raw attempt completes without needing re-prime)

This will remain environment-dependent and may be below 100% on a shared hosted CPU.

### 9.2 Eventual completion

If state-loss attempts are detectable and a fresh verified reset can be re-acquired, bounded or repeated re-prime can drive eventual completion probability very high.

This still needs a fixed-N experiment.

### 9.3 Accepted-result correctness

P(result is correct | protocol says SUCCESS)

This is the strongest 100%-oriented engineering target.

A fail-closed protocol can refuse to emit SUCCESS whenever state validity is uncertain.

The lab should optimize this before optimizing one-shot yield.

## 10. Consequence for the historical 1.6%

The historical 1.6% should no longer be viewed as:

"the final 1.6% of a 98.4%-reliable mechanism."

A better description is:

"the residual probability that a cheap admission proxy did not place the first measured touch exactly on the verified reset boundary."

The solution is therefore not necessarily a more elaborate static threshold.

It is:

predict -> normalize -> verify -> execute -> commit

with re-prime on invalidation.

## 11. 100% program

Before another large b63 reliability run:

1. promote OBS-006 direct charge receipts into the controlled-spawn observer;
2. allow calibration to continue through recognized release-only events instead of stopping on net negative deltas;
3. add explicit state-invalidated / re-prime transitions;
4. minimize cross-memcg activity on the stock CPU during the critical section;
5. verify that every accepted target result has an uninterrupted receipt chain;
6. only then run a fixed-N certification of:
   - accepted-result correctness;
   - re-prime frequency;
   - attempts-to-completion distribution;
   - maximum observed normalization depth.

The research target has changed from:

"make the first touch lucky 100% of the time"

to:

"make the protocol know exactly when it is in the right state, and never commit a result from the wrong state."
