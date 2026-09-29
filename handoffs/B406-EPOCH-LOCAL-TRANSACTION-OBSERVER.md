# B406 — Epoch-local transaction observer

## Status

COMPLETE / PREFLIGHT ONLY / NO PHYSICAL RUN.

## Implemented

- schemas/TRANSACTION-RECEIPT-PACKET-v2.schema.json
- src/finite_ram_lab/transaction_trace_observer.py
- tests/test_transaction_trace_observer.py
- docs/OBS-007-EPOCH-LOCAL-TRANSACTION-OBSERVER.md

## Main result

Chapter II requires an epoch-local target page-counter identity.

A RELEASE_ONLY event on a ZERO touch cannot identify its owner from the same window because no direct charge occurs there.

Therefore:

1. the verified direct-Q64 NORMALIZE window discovers owner_counter;
2. the counter is carried across the epoch;
3. release attribution requires matching owner counter plus the shared-LRU 31-page flush/put signature;
4. owner counter authority is destroyed at REPRIME.

## Packet v2

Adds:

- touch_index_since_verified
- elapsed_ns_since_verified
- expected_residual_before/after
- owner_counter
- marker timestamps
- unknown_emission_count

The verification touch is hazard age zero.

## Fail closed

- malformed PRE/POST markers -> trace incomplete
- owner uncharge without complete LRU signature -> UNKNOWN_EMISSION
- counter change inside one epoch -> unknown / trace gap path
- net memory.current never authorizes state

## CI

Observer source and observer unit tests passed CI.

## Next

Bind observer state to reducer/re-prime state so caller code cannot accidentally carry epoch-local authority across a re-prime.
