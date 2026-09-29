# B403 — Controlled-spawn transactional bridge preflight

## Status

COMPLETE / PREFLIGHT IMPLEMENTATION / NO PHYSICAL RUN.

## Objective

Bridge the controlled-spawn b62/b63/b64 experiment family into the B400 transaction packet model without using net memory.current as an authority signal.

## Implemented

- src/finite_ram_lab/controlled_spawn_transaction_bridge.py
- tests/test_controlled_spawn_transaction_bridge.py
- docs/CONTROLLED-SPAWN-TRANSACTION-BRIDGE-v1.md

## Main design result

The terminal controlled-spawn endpoint is a multi-touch pattern:

- b62: ZERO -> ZERO -> Q64
- b63: ZERO -> Q64
- b64: Q64

The expected final Q64 must not pass through ordinary CONSUME semantics, because B400 correctly treats refill during ordinary consumption as an invalidator.

Therefore the bridge uses an arm-level TARGET bundle:

1. collect all terminal touches;
2. apply guards to every touch;
3. derive direct ZERO/Q64 transition tokens from observer receipts;
4. compare the token vector with the frozen arm pattern;
5. emit one TARGET packet.

This preserves the distinction:

- Q64 during bait -> INVALIDATED / UNEXPECTED_REFILL
- Q64 at the wrong valid terminal phase -> TARGET_FAIL
- partial charge/refill receipt -> INVALIDATED / TRACE_GAP
- expected terminal Q64 -> TARGET_MATCH
- PTE growth anywhere in terminal bundle -> INVALIDATED

## Direct token rule

ZERO:

- no direct charge64;
- no refill63;
- complete trace;
- optional positively classified release-only.

Q64:

- exactly one direct page_counter_try_charge(64);
- exactly one refill_stock(63);
- complete trace;
- optional positively classified release-only.

Net memory.current is not consulted by token classification.

## CI

The code commit and synthetic transaction tests passed main CI.

Covered:

- masked Q64 + release;
- release-only consume;
- unexpected refill invalidation;
- unknown-emission fail-closed;
- b62/b63 terminal bundles;
- genuine early-Q64 TARGET_FAIL;
- partial-Q64 TRACE_GAP;
- PTE precedence.

## Remaining integration gap

The current physical controlled-spawn runner still lacks native per-touch trace-marker and direct observer wiring.

Required before a pilot:

- transaction trace windows;
- charge64/refill63 probes;
- drain receipts;
- positive release-only classifier;
- trace completeness;
- epoch packet archive;
- bounded REPRIME orchestration.

## Authority

PHYSICAL PAUSE.

No local-PC execution.
No paid runner.
No physical certification run.

## Next

Design the smallest information-maximizing transactional pilot and its re-prime budget only after native observer wiring is specified.
