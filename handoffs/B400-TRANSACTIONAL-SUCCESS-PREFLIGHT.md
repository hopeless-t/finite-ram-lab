# B400 — Transactional success validator preflight

## Status

PRE-FLIGHT ARCHITECTURE COMPLETE / NO NEW PHYSICAL RUN.

## Why B400 exists

The historical 98.374% REMOTE_LOW success metric was a first-touch admission metric.

B399 reframed the correctness target as:

P(correct result | protocol emits SUCCESS)

B400 turns that reframe into executable preflight architecture.

## Implemented

### State machine

src/finite_ram_lab/transactional_reprime.py

States:

- INIT
- NORMALIZING
- VERIFIED
- EXECUTING
- INVALIDATED
- COMMIT_READY
- SUCCESS
- TARGET_FAIL
- ABORTED

### Receipt packet

schemas/TRANSACTION-RECEIPT-PACKET-v1.schema.json

### Receipt adapter

src/finite_ram_lab/transactional_receipt_adapter.py

### Frozen semantics

specs/TRANSACTIONAL-REPRIME-v1.json

### Math

docs/MATH-018-TRANSACTIONAL-REPRIME-RELIABILITY.md

### Council

docs/COUNCIL-2026-09-30-TRANSACTIONAL-SUCCESS-v1.md

### Adapter contract

docs/TRANSACTIONAL-REPRIME-RECEIPT-ADAPTER-v1.md

## Direct Q64 token

VERIFIED can open only with:

- page_counter_try_charge(64)
- refill_stock(63)
- PTE clean
- CPU match
- trace complete

Net memory.current cannot authorize VERIFIED.

## Invalidation

The current epoch is invalidated by:

- unexpected refill
- drain_stock
- PTE growth
- CPU mismatch
- worker error
- trace gap

INVALIDATED attempts are NO_RESULT and may re-prime.

## Release-only rule

A positively classified LRU release is state-preserving.

It may coexist with:
- DIRECT_Q64
- EXPECTED_CONSUME

It does not decrement stock residual.

Unknown negative emissions do not receive this privilege.

## Scientific failure rule

A target mismatch after an uninterrupted verified epoch is:

TARGET_FAIL

It is terminal.

It must not be retried away.

## Epoch rule

REPRIME opens a new epoch.

Old-epoch receipts cannot authorize current SUCCESS.

## Re-prime budget

Bounded.

Budget exhaustion:

ABORTED / NO_RESULT

not TARGET_FAIL.

## CI / model-check

Current tests cover:

- every invalidator blocks SUCCESS in the current epoch;
- re-prime requires a fresh Q64 token;
- release-only remains orthogonal to expected stock residual;
- valid TARGET_FAIL cannot be re-primed;
- commit requires a complete verified chain;
- stale epoch packets are rejected;
- partial Q64 receipt pair fails closed;
- drain takes precedence over apparent target match;
- masked +64/-17 packet opens VERIFIED correctly;
- release+consume decrements residual exactly once.

Latest full CI after adapter integration:
PASS.

## Statistical meaning

Do not collapse into one success rate.

Future certification should separately report:

1. accepted-result correctness
2. genuine TARGET_FAIL rate
3. re-prime burden
4. abort / abstention rate

Zero false accepts require approximately:

- 59 accepted samples for 95% correctness floor at one-sided 95%
- 299 for 99%
- 2,995 for 99.9%
- 29,956 for 99.99%

These are planning numbers, not current claims.

## Next

No physical run yet.

Next preflight bounce:

1. build a controlled-spawn receipt adapter using existing OBS-006 semantics;
2. replay historical controlled-spawn / OBS-006 evidence into the new state machine where source receipts permit;
3. verify that historical frozen endpoints remain unchanged;
4. freeze a bounded re-prime budget and certification metrics;
5. only then design a small transactional physical pilot.

## Authority

PHYSICAL PAUSE.

No local-PC execution.
No paid runner.
No large b63 certification run.
