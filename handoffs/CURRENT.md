# CURRENT

> Latest bounce: B408
> Stage: CHAPTER II NATIVE TRANSACTION OBSERVER PREFLIGHT
> Stop: PHYSICAL PAUSE / READY FOR SUCCESSOR RUNNER ORCHESTRATION

## Chapter II question

Once a Q64 reset is directly verified:

> which events preserve the epoch, which events destroy it, and can the protocol prove the difference before COMMIT?

## Leading hypothesis

Verified stock arithmetic remains deterministic until a discrete observer-visible state-changing event occurs.

Candidate invalidators:

- unexpected refill
- drain
- PTE growth
- CPU mismatch
- worker error
- trace gap

Positively classified shared-LRU release is state-preserving.

## Historical boundary

Do not recollect the natural-state corpus.

Do not reinterpret historical controlled-spawn as B400 certification.

Frozen historical endpoints remain:

- strict controlled-spawn: 49/72
- primer-qualified terminal pattern match: 55/55

B400 accepted correctness remains historically non-identifiable.

## B405 Chapter II perturbation matrix

Frozen:

- CLEAN x4
- RELEASE_ONLY x4
- UNEXPECTED_REFILL x4
- PTE_GROWTH x4

Artifacts:

- specs/TX-PERTURBATION-MATRIX-v1.json
- docs/MATH-021-CHAPTER-II-TRANSACTION-PERTURBATION-MATRIX.md
- handoffs/B405-CHAPTER-II-PERTURBATION-MATRIX.md

B405 launches only after B404 protocol smoke passes.

## B406 epoch-local transaction observer

Implemented:

- schemas/TRANSACTION-RECEIPT-PACKET-v2.schema.json
- src/finite_ram_lab/transaction_trace_observer.py
- tests/test_transaction_trace_observer.py
- docs/OBS-007-EPOCH-LOCAL-TRANSACTION-OBSERVER.md
- handoffs/B406-EPOCH-LOCAL-TRANSACTION-OBSERVER.md

### Epoch owner identity

A verified direct-Q64 NORMALIZE window discovers:

`owner_counter(epoch)`

The counter is carried only within that epoch.

A release-only ZERO touch can therefore be attributed to the target cgroup even when the release is triggered by another task.

Positive RELEASE_ONLY requires:

- page_counter_uncharge(...,17) on owner_counter
- LRU flush nr=31
- folios_put nr=31
- complete marker window

Owner uncharge without the complete LRU signature is UNKNOWN and fails closed.

### Hazard coordinates

Packet v2 adds:

- touch_index_since_verified
- elapsed_ns_since_verified
- expected_residual_before
- expected_residual_after
- owner_counter
- marker timestamps
- unknown_emission_count

The verified Q64 touch is hazard age zero.

## B407 epoch archive

Implemented:

- src/finite_ram_lab/transaction_epoch_archive.py
- tests/test_transaction_epoch_archive.py
- docs/TX-ARCHIVE-001-EPOCH-LOCAL-REPLAY.md
- handoffs/B407-EPOCH-LOCAL-ARCHIVE-REPLAY.md

### Re-prime invariant

REPRIME destroys both transaction and observer authority:

- old owner_counter cleared
- verified_at_ns cleared
- touch-age clock cleared
- old epoch packets rejected

Synthetic sentinel replay:

epoch0:
direct Q64 owner 0xaaa -> VERIFIED -> unexpected refill -> INVALIDATED

hard re-prime:
epoch -> 1, owner -> NULL

epoch1:
fresh direct Q64 owner 0xbbb -> valid target -> COMMIT -> SUCCESS

The invalidating Q64 cannot become the next epoch primer.

Synthetic archive replay passed CI.

## B408 native marker wrapper

Implemented:

- src/finite_ram_lab/transactional_spawn_native.py
- tests/test_transactional_spawn_native.py
- handoffs/B408-NATIVE-TRANSACTION-MARKER-WRAPPER.md

The frozen Chapter-I _touch() primitive remains unchanged.

Chapter-II successor wraps it as:

FRL_TX PRE
-> historical _touch()
-> FRL_TX POST

POST is emitted from a finally block.

A missing readback window fails closed.

No physical workflow or launch marker was created.

## Current capture model

The highest-value candidate rare event is now:

> canonical stock phase changes while the observer reports no invalidator.

If this occurs with complete receipts, it becomes evidence for a missing state-changing mechanism.

That is the Chapter-II rare-pokemon target.

## Next

Implement the successor transactional-spawn runner orchestration:

1. hard-new-worker epoch lifecycle
2. P-side PTE precondition
3. migrate to stock CPU
4. bounded NORMALIZE using direct trace receipts
5. CONSUME packets
6. TARGET bundle
7. archive packets per epoch
8. no automatic physical launch

Then run B404 only after authorization.

## Authority

PAUSE.
No local-PC execution.
No paid runner.
No physical pilot.
No B405 perturbation matrix.
No large reliability certification.
