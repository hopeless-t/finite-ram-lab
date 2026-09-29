# CURRENT

> Latest bounce: B403
> Stage: CONTROLLED-SPAWN TRANSACTION BRIDGE PREFLIGHT COMPLETE
> Stop: PHYSICAL PAUSE / READY FOR NATIVE TRACE WIRING + PILOT DESIGN

## Core semantic result

The lab no longer uses one binary SUCCESS/FAIL axis for all evidence.

Separate:

1. raw observations;
2. hidden-state interpretation;
3. transactional certification.

Natural exact-zero datasets remain reusable.

Transactional correctness requires B400-native direct receipts.

## Historical-data decision

Do not recollect the natural-state corpus.

Do not globally refit MATH-001..018 merely because terminology changed.

Controlled-spawn v2 remains historically frozen:

- strict 49/72;
- primer-qualified terminal pattern 55/55.

Neither value estimates B400 accepted-result correctness.

Historical B400 true success and true TARGET_FAIL probabilities are non-identifiable because the direct charge64 + refill63 receipt chain was not recorded.

## B402 assumption audit

Machine-readable:

- analysis/inputs/ASSUMPTION-DEPENDENCY-AUDIT-v1.json

Narrative:

- docs/MATH-019-SEMANTIC-DEPENDENCY-AUDIT.md

Key result:

most natural-state mathematics survives numerically with a changed estimand.

MATH-015's old H17-STOCK/drain origin is superseded by OBS-005/MATH-016 shared-LRU handoff evidence.

## B403 bridge implementation

Implemented:

- src/finite_ram_lab/controlled_spawn_transaction_bridge.py
- tests/test_controlled_spawn_transaction_bridge.py
- docs/CONTROLLED-SPAWN-TRANSACTION-BRIDGE-v1.md
- handoffs/B403-CONTROLLED-SPAWN-TRANSACTION-BRIDGE.md

### Direct transition tokens

ZERO:

- complete trace;
- no direct charge64;
- no refill63;
- optional classified release-only.

Q64:

- exactly one page_counter_try_charge(64);
- exactly one refill_stock(63);
- complete trace;
- optional classified release-only.

Net memory.current is not authoritative.

### Terminal bundle rule

b62/b63/b64 are multi-touch terminal patterns:

- b62: ZERO -> ZERO -> Q64
- b63: ZERO -> Q64
- b64: Q64

The expected terminal Q64 must not be routed through ordinary CONSUME semantics.

The bridge therefore validates the whole terminal sequence and emits one TARGET packet.

This distinguishes:

- Q64 during bait -> INVALIDATED / UNEXPECTED_REFILL
- Q64 at wrong valid terminal phase -> TARGET_FAIL
- partial charge/refill -> INVALIDATED / TRACE_GAP
- expected terminal Q64 -> TARGET_MATCH
- PTE growth -> INVALIDATED regardless of apparent pattern match

## CI

Bridge source CI: PASS.

Bridge synthetic tests CI: PASS.

Continuity Observer for the tested bridge commit: PASS.

## Remaining physical integration gap

The current controlled-spawn runner does not yet emit all source-grounded per-touch receipts required by the bridge.

Before any pilot, wire:

- transaction trace markers;
- page_counter_try_charge(64);
- refill_stock(63);
- drain_stock;
- positive release-only classification;
- trace completeness;
- per-epoch packet archive;
- bounded REPRIME orchestration.

## Research topology

### Track N — Natural Hidden-State Ecology

Reuse historical samples for:

- CAP10-neighborhood association;
- initial residual state;
- depth1/deep tail;
- PTE perturbation;
- normalization burden prediction.

### Track T — Transactional Correctness

New B400-native samples only for:

- verified reset acquisition;
- invalidation causes;
- re-prime burden;
- genuine TARGET_FAIL;
- accepted-result correctness;
- abort/abstention.

### Bridge

X -> normalization burden -> verified reset -> target transition

replaces:

X -> SUCCESS/FAIL

## Next

Specify native trace wiring and choose the smallest information-maximizing transactional pilot.

Do not launch a large b63 reliability certification yet.

## Authority

PAUSE.
No local-PC execution.
No paid runner.
No physical certification run.
