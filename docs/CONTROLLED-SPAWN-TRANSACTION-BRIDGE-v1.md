# CONTROLLED-SPAWN -> TRANSACTION-RECEIPT-PACKET Bridge v1

> Status: PREFLIGHT IMPLEMENTED / NO PHYSICAL RUN

## Purpose

Connect the existing controlled-spawn b62/b63/b64 experiment family to the B400 transactional validator without reintroducing net-memory.current inference.

Implementation:

- src/finite_ram_lab/controlled_spawn_transaction_bridge.py
- tests/test_controlled_spawn_transaction_bridge.py

The bridge consumes source-grounded observer receipts and emits:

- NORMALIZE packets
- CONSUME packets
- one arm-level TARGET bundle packet

## Why a target bundle is necessary

The controlled-spawn endpoint is not one touch.

Expected terminal sequences are:

- b62: ZERO -> ZERO -> Q64
- b63: ZERO -> Q64
- b64: Q64

If every post-primer touch were sent through the ordinary CONSUME adapter, the expected terminal Q64 would be classified as UNEXPECTED_REFILL.

That would be semantically wrong.

Therefore terminal pattern evaluation is a separate operation:

1. collect every terminal touch with source-grounded receipts;
2. apply invalidation guards to every constituent touch;
3. convert each touch to a direct transition token;
4. compare the complete observed token vector with the frozen arm pattern;
5. emit one TARGET packet.

## Direct transition token

For a measured data-page touch:

### ZERO

Requires:

- trace complete;
- no unknown emission;
- no page_counter_try_charge(64);
- no refill_stock(63).

A classified release-only emission may coexist.

Net memory.current is ignored.

### Q64

Requires exactly one paired direct observation:

- page_counter_try_charge(64);
- refill_stock(63).

A classified release-only emission may coexist.

Net memory.current is ignored.

### INCOMPLETE

Any of:

- trace incomplete;
- unknown emission;
- charge64 without refill63;
- refill63 without charge64.

This fails closed as TRACE_GAP.

### OTHER

A complete but noncanonical charge/refill multiplicity.

Inside TARGET this produces a target mismatch rather than silently normalizing it away.

## NORMALIZE

Each calibration touch becomes one NORMALIZE packet.

A paired direct Q64 opens VERIFIED.

Release-only may coexist.

A negative net memory.current value alone never ends normalization.

Unknown negative emissions fail closed.

## CONSUME

Each bait touch becomes one CONSUME packet.

Expected behavior:

- no direct Q64 pair;
- optional classified release-only;
- guards clean.

A direct Q64/refill during bait is UNEXPECTED_REFILL and invalidates the epoch.

This is state loss before the target, not TARGET_FAIL.

## TARGET bundle

The bridge evaluates the whole b62/b63/b64 terminal sequence.

Examples:

### b63 expected

ZERO -> Q64

Observed direct tokens:

ZERO -> Q64

Result:

TARGET_MATCH.

### b63 early Q64

Q64 -> ZERO

If all receipts are complete and no invalidator fires:

TARGET_MISMATCH -> TARGET_FAIL.

This is a genuine scientific mismatch because the verified epoch remained observable and the transition occurred at the wrong phase.

### Partial expected Q64

charge64 without refill63:

TRACE_GAP -> INVALIDATED.

Do not call it TARGET_FAIL.

### PTE growth with otherwise correct pattern

PTE_GROWTH -> INVALIDATED.

Guard precedence remains stronger than TARGET_MATCH.

## Release-only rule

The bridge never infers release-only from a negative net delta.

The observer must supply:

classified_release_only_count

based on source-grounded OBS-005/006 logic.

Thus historical -13/-3/-2-like unknown emissions remain fail-closed until an observer can classify them.

## Important state-machine consequence

B400's generic state machine can remain unchanged for this bridge.

The arm-specific evaluator owns the multi-touch terminal sequence and emits one TARGET result only after all constituent guards have been checked.

This keeps:

- generic transaction semantics generic;
- b62/b63/b64 pattern knowledge outside the core reducer.

## Current unit coverage

Synthetic tests cover:

- masked Q64 + release opens VERIFIED;
- release-only during consume preserves state and decrements residual once;
- unexpected Q64 during bait invalidates;
- unknown emission fails closed;
- release-only does not change ZERO/Q64 transition token;
- b63 direct terminal pattern reaches COMMIT_READY and SUCCESS after COMMIT;
- b62 release contamination remains pattern-preserving;
- early Q64 in b63 becomes genuine TARGET_FAIL;
- partial terminal Q64 becomes TRACE_GAP;
- PTE growth overrides an otherwise matching terminal pattern.

## What is still missing

This is not yet a physical bridge.

The existing controlled-spawn runner does not yet emit the trace-marker windows and normalized source-grounded observer records required by this module.

Next integration work must add:

1. per-touch transaction trace markers;
2. direct charge64/refill63 probes;
3. drain_stock receipts;
4. positive LRU release classification;
5. trace completeness accounting;
6. packet archive per epoch;
7. bounded REPRIME orchestration.

No physical pilot should launch until those pieces are wired and CI/model checks remain green.

## Authority

PRE-FLIGHT ONLY.

No local-PC execution.
No paid runner.
No physical certification launch.
