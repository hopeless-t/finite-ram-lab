# CURRENT

> Latest bounce: B404
> Stage: MINIMAL TRANSACTIONAL SPAWN PILOT DESIGN FROZEN
> Stop: PHYSICAL PAUSE / READY FOR NATIVE TRACE-OBSERVER WIRING

## Core research split

finite-ram-lab now has two linked but distinct research tracks.

### Track N — Natural Hidden-State Ecology

Historical natural panels remain reusable for:

- CAP10-neighborhood association;
- initial residual phase;
- depth1/deep tail;
- PTE perturbation;
- normalization burden prediction.

These are not target correctness measurements.

### Track T — Transactional Correctness

New B400-native receipts are required for:

- verified reset acquisition;
- invalidation causes;
- re-prime burden;
- genuine TARGET_FAIL;
- accepted-result correctness;
- abort/abstention.

Bridge:

X -> normalization burden -> verified reset -> target transition

replaces the old:

X -> SUCCESS/FAIL

## Historical-data decision

Do not recollect the natural-state corpus.

Do not globally refit MATH-001..018 solely because semantics changed.

Controlled-spawn v2 remains frozen:

- strict 49/72;
- primer-qualified terminal pattern 55/55.

B400 true accepted correctness is historically non-identifiable.

The historical replay ledger explicitly distinguishes zero certified accepts from an empirical 0% success rate.

## B402 assumption audit

- analysis/inputs/ASSUMPTION-DEPENDENCY-AUDIT-v1.json
- docs/MATH-019-SEMANTIC-DEPENDENCY-AUDIT.md
- handoffs/B402-ASSUMPTION-DEPENDENCY-AUDIT.md

Key result:

most natural-state mathematics survives numerically with changed estimands.

MATH-015 H17-STOCK/drain origin is superseded by OBS-005/MATH-016 shared-LRU handoff evidence.

## B403 bridge

Implemented:

- src/finite_ram_lab/controlled_spawn_transaction_bridge.py
- tests/test_controlled_spawn_transaction_bridge.py
- docs/CONTROLLED-SPAWN-TRANSACTION-BRIDGE-v1.md
- handoffs/B403-CONTROLLED-SPAWN-TRANSACTION-BRIDGE.md

Bridge semantics:

- direct ZERO/Q64 tokens ignore net memory.current;
- release-only may coexist;
- bait Q64 -> INVALIDATED;
- wrong valid terminal phase -> TARGET_FAIL;
- partial Q64 pair -> TRACE_GAP;
- terminal b62/b63/b64 pattern -> TARGET bundle.

Bridge source and synthetic tests passed CI.

## B404 minimal pilot

Frozen design:

- specs/TRANSACTIONAL-SPAWN-PILOT-v1.json
- docs/MATH-020-TRANSACTIONAL-SPAWN-PILOT-DESIGN.md
- handoffs/B404-MINIMAL-TRANSACTIONAL-PILOT-DESIGN.md

### Normal lane

12 scientific identities:

- b62 = 4
- b63 = 4
- b64 = 4

No replacement identities.

This is protocol smoke only.

Even 12/12 correct accepted results imply only about a 77.9% one-sided 95% all-success correctness floor.

No reliability claim is permitted.

### Sentinel lane

One non-scientific:

FORCED_UNEXPECTED_REFILL_THEN_HARD_REPRIME

Purpose:

- prove invalidated epoch cannot commit;
- prove stale epoch receipts cannot authorize a new epoch;
- prove fresh direct Q64 is required after re-prime.

### Re-prime baseline

- max_reprimes = 2
- mode = HARD_NEW_WORKER_CGROUP
- maximum 3 epochs per identity

Hard re-prime is the first baseline because it gives:

- stronger epoch isolation;
- clean receipt boundaries;
- fresh safe-span budget;
- less direct carry-over from an invalidated worker.

Soft same-worker re-prime is deferred as an optimization study.

### Stop rules

Immediate scientific stop:

- any TARGET_FAIL from a complete uninterrupted verified normal-lane epoch.

Instrumentation hold:

- trace gap;
- CPU mismatch;
- worker error.

State invalidation:

- unexpected refill;
- drain;
- PTE growth.

These may hard re-prime while budget remains.

Budget exhaustion:

ABORTED / NO_RESULT.

No automatic scale expansion.

## Remaining integration gap

Before any physical pilot, wire:

- per-touch transaction markers;
- page_counter_try_charge(64);
- refill_stock(63);
- drain_stock;
- positive release-only classification;
- trace completeness;
- per-epoch packet archive;
- hard re-prime orchestration.

## Next

Implement native trace/observer wiring and synthetic end-to-end epoch archive replay.

Do not launch the physical pilot until wiring, CI, and Human authorization boundaries are satisfied.

## Authority

PAUSE.
No local-PC execution.
No paid runner.
No physical pilot.
No large b63 reliability certification.
