# COUNCIL — Transactional success / re-prime promotion

> Date: 2026-09-30
> Status: CONVERGED / DESIGN PROMOTION ONLY / NO PHYSICAL RUN

## Roles

1. mechanism scientist
2. observer / instrumentation engineer
3. statistical reliability
4. kernel-concurrency reviewer
5. falsification / red-team
6. maintainer / scope control

## Question

Should the historical SUCCESS/FAIL classifier be promoted from first-touch / net-delta classification to a verified transactional state machine?

## Round 1 — What does SUCCESS mean?

Mechanism:
SUCCESS must mean a target transition from a known Q64 reset state.

Observer:
net memory.current cannot authorize SUCCESS because +64 can be masked by release and non-Q64 emissions can mimic net deltas.

Statistics:
first-attempt yield and accepted-result correctness are different estimands.

Resolution:

SUCCESS is a committed result from one uninterrupted verified epoch.

Required reset token:

- page_counter_try_charge(64)
- refill_stock(63)
- PTE clean
- CPU match
- trace complete

Converged: 6/6.

## Round 2 — What is a failure?

Conflict:

A retry-oriented controller could be tempted to classify every mismatch as INVALIDATE and retry.

Red-team rejects this because it could retry away falsifying evidence.

Resolution:

Two categories are mandatory.

### State invalidation / NO_RESULT

- unexpected refill
- drain_stock
- PTE growth
- CPU mismatch
- worker error
- trace gap
- normalization exhaustion

These may RE-PRIME.

### Genuine TARGET_FAIL

If:
- verified reset exists;
- receipt chain is complete;
- no invalidation occurred;
- frozen target pattern mismatches;

then TARGET_FAIL is terminal and must not be retried away.

Converged: 6/6.

## Round 3 — What about LRU release?

OBS-001..005 show recurrent -17 release is observer/accounting emission, not stock consumption.

Resolution:

A release event may be treated as state-preserving only when positively classified as release-only.

Unclassified negative delta is not equivalent to RELEASE_ONLY.

It must remain UNKNOWN / invalidate through observer incompleteness.

Converged: 6/6.

## Round 4 — Is re-prime allowed to be unbounded?

No.

Unbounded retries can:
- hide pathological interference;
- make eventual completion unfalsifiable;
- create unbounded cost;
- blur availability and correctness.

Resolution:

Re-prime budget must be finite and frozen before a run.

Budget exhaustion -> ABORTED / NO_RESULT.

Never TARGET_FAIL.

Converged: 6/6.

## Round 5 — What is the 100% target?

Rejected target:

P(first touch is Q64) = 1

Primary engineering target:

P(correct | protocol emits SUCCESS)

Secondary operational targets:

- eventual completion under bounded re-prime;
- re-prime burden;
- abort rate.

Scientific falsification target:

TARGET_FAIL / uninterrupted verified executions.

Converged: 6/6.

## Round 6 — Is the current state machine ready for physical promotion?

Current implementation:

src/finite_ram_lab/transactional_reprime.py

Current design math:

docs/MATH-018-TRANSACTIONAL-REPRIME-RELIABILITY.md

Strengths:

- explicit epochs;
- direct Q64 receipt token;
- RELEASE_ONLY orthogonal to residual stock;
- invalidators fail closed;
- valid mismatch terminal;
- bounded re-prime;
- memory.current has no authoritative event.

Remaining before physical promotion:

1. adapter from trace/worker receipts into normalized Event stream;
2. replay against existing controlled-spawn / OBS-006 evidence;
3. model-check receipt ordering, including simultaneous charge+release windows;
4. freeze re-prime budget and certification metrics;
5. verify no historical frozen endpoint is rewritten.

Resolution:

PROMOTE TO PRE-FLIGHT ARCHITECTURE.

DO NOT YET PROMOTE TO PHYSICAL CERTIFICATION.

Converged: 6/6.

## Statistical planning note

Zero false accepts do not prove zero error.

With zero false accepts, approximate accepted samples required for a one-sided 95% correctness floor:

- 95%: 59
- 99%: 299
- 99.9%: 2,995
- 99.99%: 29,956

Do not choose a certification target after seeing the data.

## Final Council statement

The classifier has changed from a binary observation classifier into a transaction validator.

The key distinction is:

**attempt outcome != scientific result**

An invalidated attempt is discarded and may re-prime.

A genuine target mismatch from a verified uninterrupted epoch is scientific failure and must remain visible.

This design is the correct basis for the next controlled-spawn generation.
