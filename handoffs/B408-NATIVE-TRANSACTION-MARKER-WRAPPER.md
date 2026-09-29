# B408 — Native transaction marker wrapper

## Status

IMPLEMENTED / PREFLIGHT ONLY / NO PHYSICAL RUN.

## Objective

Add Chapter-II FRL_TX trace windows without modifying the frozen Chapter-I controlled-spawn touch primitive.

## Implemented

- src/finite_ram_lab/transactional_spawn_native.py
- tests/test_transactional_spawn_native.py

## Design

The historical function:

`memcg005gc_controlled_spawn._touch()`

is unchanged.

The Chapter-II successor uses:

`touch_with_transaction_marker()`

which performs:

1. FRL_TX PRE
2. historical _touch()
3. FRL_TX POST

POST is emitted from a finally block even if the Python wrapper sees an exception.

This preserves the old experimental code path while adding a new observation envelope.

## Marker identity

Every window binds:

- trial_id
- epoch
- phase
- touch_number
- PRE/POST edge

No marker omits epoch.

## Readback

The native helper can read the trace log after a completed touch and produce the OBS-007 epoch-aware receipt.

A missing window becomes marker_error_count=1 and fails closed.

## Tests

Synthetic tests cover:

- exact epoch-scoped marker format
- POST marker on wrapper exception
- missing-window fail closed
- direct-Q64 owner discovery from native readback

## Remaining gap

The successor pilot runner still needs orchestration for:

- worker lifecycle per hard-reprime epoch
- P-side PTE precondition
- migration to stock CPU
- bounded NORMALIZE
- CONSUME
- TARGET bundle
- packet archive persistence

No physical workflow or launch marker was created in this bounce.

## Authority

PAUSE.
No local-PC execution.
No paid runner.
No physical pilot.
