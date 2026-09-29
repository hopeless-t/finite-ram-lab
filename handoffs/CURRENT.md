# CURRENT

> Latest bounce: B401
> Stage: HISTORICAL TRANSACTIONAL REPLAY COMPLETE
> Stop: PHYSICAL PAUSE / READY FOR NATIVE CONTROLLED-SPAWN TRANSACTION BRIDGE

## Success semantics

SUCCESS is no longer first-touch luck or net memory.current.

Canonical path:

predict -> normalize -> verify -> execute -> commit

Verified Q64 token requires:

- page_counter_try_charge(64)
- refill_stock(63)
- PTE clean
- CPU match
- trace complete

## Outcomes

SUCCESS:
complete verified epoch + target match + commit.

TARGET_FAIL:
verified uninterrupted epoch + genuine target mismatch.

NO_RESULT:
state invalidation -> REPRIME, bounded-budget ABORT, or legacy receipt gap in historical replay.

Do not retry TARGET_FAIL away.

## B401 historical replay

Frozen historical endpoints remain unchanged.

Controlled-spawn v2 remains:

- strict 49/72
- primer found 55/72
- primer-qualified terminal match 55/55

B400 replay of that historical target run:

- TX_SUCCESS = 0
- TX_TARGET_FAIL = 0
- TX_NO_RESULT_RECEIPT_GAP = 72

Reason:
the run predates the required direct charge64 + refill63 receipt pair.

This is a certification gap, not a performance estimate.

OBS-006 corrected:

- 14/16 -> TX_NONTERMINAL_VERIFIED
- 2/16 -> TX_NO_RESULT_INVALIDATED / unexpected refill
- 0 -> TX_TARGET_FAIL

G0 LOW PTE-growth subset:

- historical net-Q64 5/5
- B400 -> 5/5 TX_NO_RESULT_INVALIDATED / PTE_GROWTH

MEMCG-005F first-touch zeros and G-A biopsies are now explicitly pre-transaction initial-state / normalization observations, not target failures.

No historical observation currently demonstrates a genuine target mismatch after a B400-complete verified uninterrupted epoch.

That is not a zero-failure probability claim.

## Replay artifacts

- analysis/inputs/HISTORICAL-TRANSACTION-REPLAY-v1.json
- docs/RETROSPECTIVE-TRANSACTIONAL-RECLASSIFICATION-v1.md
- handoffs/B401-HISTORICAL-TRANSACTION-REPLAY.md

## Existing implementation

- src/finite_ram_lab/transactional_reprime.py
- src/finite_ram_lab/transactional_receipt_adapter.py
- specs/TRANSACTIONAL-REPRIME-v1.json
- schemas/TRANSACTION-RECEIPT-PACKET-v1.schema.json
- docs/MATH-018-TRANSACTIONAL-REPRIME-RELIABILITY.md
- docs/COUNCIL-2026-09-30-TRANSACTIONAL-SUCCESS-v1.md
- docs/TRANSACTIONAL-REPRIME-RECEIPT-ADAPTER-v1.md

## Next

Build the native controlled-spawn -> TRANSACTION-RECEIPT-PACKET bridge.

The next small physical pilot must emit the complete B400 chain from the start:

- NORMALIZE direct charge/refill receipts
- classified release-only emissions
- PTE/CPU/worker/trace guards
- CONSUME packets
- TARGET packet
- COMMIT
- bounded REPRIME

Do not launch a large b63 reliability certification yet.

## Authority

PAUSE.
No local-PC execution.
No paid runner.
No large b63 certification run.
