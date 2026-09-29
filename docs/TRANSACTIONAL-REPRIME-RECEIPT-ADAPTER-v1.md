# TRANSACTIONAL-REPRIME receipt adapter contract v1

> Status: PRE-FLIGHT CONTRACT / NO PHYSICAL RUN

## Purpose

Separate raw observer evidence from transaction state transitions.

The state machine must never infer semantics directly from net memory.current.

Each measured touch is first normalized into one receipt packet.

Schema:

schemas/TRANSACTION-RECEIPT-PACKET-v1.schema.json

## Precedence

Receipt interpretation is fail-closed.

For each packet:

1. trace_complete == false
   -> TRACE_GAP

2. worker_ok == false
   -> WORKER_ERROR

3. cpu_match == false
   -> CPU_MISMATCH

4. vmpte_delta_kib != 0
   -> PTE_GROWTH

5. drain_stock_count > 0
   -> DRAIN_STOCK

Only if none of the above fired may positive state transitions be considered.

## NORMALIZE

A verified Q64 reset requires in the same normalized packet:

- page_counter_try_charge_64_count >= 1
- refill_stock_63_count >= 1
- trace complete
- CPU match
- worker OK
- VmPTE clean

Then:

DIRECT_Q64

If a classified LRU release occurs in the same packet, record RELEASE_ONLY after opening the verified reset.

The release does not change expected stock residual.

A lone release without Q64:

RELEASE_ONLY

and normalization continues.

A partial Q64 pair, such as charge64 without refill63 or refill63 without a complete paired receipt, must not open VERIFIED.

Treat as observer-incomplete / TRACE_GAP unless a more specific receipt explains it.

## CONSUME

If an unexpected refill appears:

UNEXPECTED_REFILL

Do not also count the touch as successful expected consumption.

Otherwise:

- classified release-only may be recorded;
- EXPECTED_CONSUME decrements the modeled residual by one.

Thus a touch may legitimately be:

RELEASE_ONLY + EXPECTED_CONSUME

without invalidating stock state.

## TARGET

The arm-specific target evaluator runs only after all invalidation guards pass.

Then it emits exactly one:

- TARGET_MATCH
- TARGET_MISMATCH

A valid mismatch is scientific failure and is terminal.

It is never converted into re-prime.

## Epoch rule

Every packet carries epoch.

Packets from an older epoch cannot authorize transitions in the current epoch.

REPRIME increments epoch and discards all previous authorization state.

## Simultaneous +64/-17 example

Raw effects:

- charge64
- refill63
- LRU release17
- net memory.current +47

Packet:

- page_counter_try_charge_64_count = 1
- refill_stock_63_count = 1
- classified_release_only_count = 1
- all guards clean

NORMALIZE result:

DIRECT_Q64
then RELEASE_ONLY

State:

VERIFIED, residual=63

Net +47 is corroboration only.

## Non-goal

This contract does not decide whether a raw kernel event is truly release-only.

That classification must be supplied by the source-grounded observer logic developed in OBS-001..006.

Unknown emissions fail closed.
