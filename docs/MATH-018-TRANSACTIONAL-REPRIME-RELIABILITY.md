# MATH-018 — Transactional re-prime reliability

> Status: DESIGN MATH / NO NEW PHYSICAL RUN
> Inputs: MEMCG-005F, G-A, controlled-spawn v2, OBS-005, OBS-006, MATH-017.

## 1. Success is no longer a one-shot Bernoulli

The historical REMOTE_LOW metric was:

- first-touch Q64: 121/123 = 98.374%
- first-touch zero: 2/123 = 1.626%

B399 changes the engineering object.

A raw attempt can now end in three semantically different ways:

1. SUCCESS
   - verified Q64 reset;
   - uninterrupted state-valid receipt chain;
   - target transition matches;
   - commit invariant passes.

2. TARGET_FAIL
   - state is verified and remains valid;
   - observer is complete;
   - target transition genuinely mismatches.

3. NO_RESULT
   - state becomes invalid or unobservable;
   - transaction is discarded;
   - protocol re-primes or eventually aborts.

NO_RESULT is neither SUCCESS nor TARGET_FAIL.

This prevents asynchronous contamination from being counted as a mechanism failure while also preventing retries from hiding a valid-state mismatch.

## 2. State-machine invariant

Canonical path:

INIT
-> NORMALIZING
-> VERIFIED
-> EXECUTING
-> COMMIT_READY
-> SUCCESS

Invalidating receipts:

- unexpected refill;
- drain_stock;
- PTE growth;
- CPU mismatch;
- worker error;
- trace/receipt gap.

Any invalidating receipt before commit causes:

ACTIVE
-> INVALIDATED
-> REPRIME
-> NORMALIZING(new epoch)

A re-prime must open a new epoch.
Receipts from the previous epoch cannot authorize SUCCESS.

Release-only LRU emissions are recorded but do not alter expected stock residual.

## 3. Mechanism failure must not be retried away

If the protocol has:

- direct verified Q64;
- complete observer receipts;
- no state invalidation;

and the frozen target pattern mismatches, the terminal state is:

TARGET_FAIL

not:

INVALIDATE -> REPRIME.

This distinction is required for scientific falsifiability.

## 4. Three reliability quantities

### 4.1 First-attempt completion

p1 = P(one raw transaction reaches a valid terminal result without re-prime)

OBS-006 deliberately adversarial masked-Q64 diagnostic observed:

14 state-preserved / 16 total = 0.875.

This is not a production estimate.
It is a design sensitivity point under one hostile constructed workload.

### 4.2 Eventual completion under re-prime

If per-attempt state-preservation probability is p and attempts were independent/stationary, completion by K attempts would be:

P_K = 1 - (1-p)^K

Using only the point estimate p=14/16 as an illustration:

- K=1: 87.5%
- K=2: 98.4375%
- K=3: 99.8047%
- K=4: 99.9756%
- K=5: 99.9969%

This arithmetic is illustrative only.

Independence and stationarity are not established.
Shared-CPU interference may be bursty and correlated.

Therefore fixed-N re-prime experiments must measure:
- attempts-to-completion distribution;
- run/block correlation;
- tail of normalization depth;
- consecutive invalidation streaks.

### 4.3 Accepted-result correctness

The primary 100%-oriented target is:

P(correct | protocol emits SUCCESS)

This is controlled by the false-accept probability, not by first-attempt yield.

A fail-closed protocol can trade yield for accepted-result correctness.

## 5. Zero observed false accepts is not proof of zero error

Suppose a certification observes zero false accepts in n accepted transactions.

The one-sided 95% Clopper-Pearson upper bound on false-accept probability is:

u = 1 - 0.05^(1/n)

Equivalently, to support an accepted-result correctness floor c with zero observed false accepts:

n >= ln(0.05) / ln(c)

Approximate required zero-error accepted samples:

- 95% correctness floor: 59
- 99% correctness floor: 299
- 99.9% correctness floor: 2,995
- 99.99% correctness floor: 29,956

Therefore literal or near-literal "100%" cannot be established by a small pilot.

The near-term goal should be protocol correctness plus a predeclared statistical certification target.

## 6. Posterior sensitivity for OBS-006 state preservation

Using Jeffreys prior Beta(0.5,0.5), the OBS-006 state-preservation observation 14/16 gives:

posterior Beta(14.5, 2.5)

Approximate 95% credible interval for per-attempt state preservation:

0.656 to 0.973

Median:

about 0.867

If independence held, propagating this uncertainty gives approximate 95% credible intervals for eventual completion:

- by 2 attempts: 0.881 to 0.999
- by 3 attempts: 0.959 to 0.99998
- by 4 attempts: 0.986 to >0.99999
- by 5 attempts: 0.995 to >0.999999

Again: this is design sensitivity, not certification.

## 7. Why the old 98.4% and the new transaction are not contradictory

The old number measured:

P(first measured touch is Q64 | REMOTE_LOW)

The new protocol targets:

P(correct commit | verified transaction)

and separately:

P(eventual valid transaction | bounded re-prime)

These are different estimands.

It is possible for:
- first-touch yield to remain below 100%;
- re-prime frequency to be nonzero;
- accepted-result correctness to approach a very high level.

## 8. Proposed certification metrics

A future fixed-N certification should freeze four metrics:

### C1 — Accepted correctness

false accepts / accepted SUCCESS transactions

Primary.

### C2 — Mechanism mismatch

TARGET_FAIL / valid uninterrupted transactions

Scientific falsification metric.

### C3 — Re-prime burden

- reprimes per completion;
- p50/p95/p99 attempts-to-completion;
- max observed attempts.

Operational metric.

### C4 — Abstention/abort

ABORTED / admitted transactions

Availability metric.

Do not collapse these four numbers into one "success rate."

## 9. Preflight property target

Before any physical certification run, the reducer must satisfy:

- no SUCCESS without DIRECT_Q64;
- no SUCCESS after an invalidating event unless a new epoch is opened and a new DIRECT_Q64 is observed;
- RELEASE_ONLY cannot alter expected residual;
- TARGET_MISMATCH with a valid chain terminates as TARGET_FAIL;
- trace gap invalidates;
- re-prime budget exhaustion produces ABORTED, never TARGET_FAIL;
- memory.current delta alone cannot authorize any state transition.

Implementation:

src/finite_ram_lab/transactional_reprime.py

## 10. Research decision

The next physical experiment should not ask:

"Did we get first-touch Q64?"

It should ask:

"Can the protocol repeatedly normalize, verify, survive or detect invalidation, re-prime, and only commit from an uninterrupted verified epoch?"

Until that state machine passes synthetic/exhaustive preflight, keep physical execution paused.
