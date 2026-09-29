# CURRENT

> Latest bounce: B405
> Stage: CHAPTER II TRANSACTION PERTURBATION MATRIX FROZEN
> Stop: PHYSICAL PAUSE / READY FOR NATIVE TRACE-OBSERVER WIRING

## Chapter II question

Once a Q64 reset is directly verified:

> which events preserve the epoch, which events destroy it, and can the protocol prove the difference before COMMIT?

## Leading hypothesis

Verified stock arithmetic remains deterministic until a discrete observer-visible state-changing event occurs.

Do not model all historical failure as one Bernoulli error process.

Current candidate invalidators:

- unexpected refill
- drain
- PTE growth
- CPU mismatch
- worker error
- trace gap

Positively classified LRU release is state-preserving.

## Why this hypothesis has traction

Historical controlled-spawn:

- strict endpoint 49/72 remains frozen
- primer-qualified terminal pattern 55/55 remains frozen
- negative bait events retained the predicted terminal phase

OBS-005 / MATH-016:

- recurrent -17 was causally grounded as shared per-CPU LRU release

Controlled-spawn v2:

- target PTE preconditioning removed measured PTE growth from the controlled sequence

OBS-006:

- direct Q64 observer recognized masked Q64
- state-loss cases were rejected as unexpected refill rather than accepted as success

The remaining high-value question is therefore release-only contamination vs true state mutation.

## B402 assumption audit

Do not recollect the natural-state corpus.

Most MATH-001..018 numerical results survive with new estimands.

Artifacts:

- analysis/inputs/ASSUMPTION-DEPENDENCY-AUDIT-v1.json
- docs/MATH-019-SEMANTIC-DEPENDENCY-AUDIT.md
- handoffs/B402-ASSUMPTION-DEPENDENCY-AUDIT.md

## B403 controlled-spawn transaction bridge

Implemented:

- src/finite_ram_lab/controlled_spawn_transaction_bridge.py
- tests/test_controlled_spawn_transaction_bridge.py
- docs/CONTROLLED-SPAWN-TRANSACTION-BRIDGE-v1.md

Core semantics:

- ZERO/Q64 derive from direct observer receipts, not net memory.current
- release-only may coexist
- bait Q64 -> INVALIDATED
- wrong valid terminal phase -> TARGET_FAIL
- partial Q64 pair -> TRACE_GAP
- terminal b62/b63/b64 sequence -> one TARGET bundle

CI passed for bridge source and tests.

## B404 first physical smoke design

Frozen:

- specs/TRANSACTIONAL-SPAWN-PILOT-v1.json
- docs/MATH-020-TRANSACTIONAL-SPAWN-PILOT-DESIGN.md

Normal lane:

- b62 x4
- b63 x4
- b64 x4

Sentinel:

- one FORCED_UNEXPECTED_REFILL_THEN_HARD_REPRIME

Re-prime:

- HARD_NEW_WORKER_CGROUP
- max_reprimes=2

This is protocol smoke only, not reliability certification.

B404 must pass before Chapter II perturbation experiments launch.

## B405 Chapter II perturbation matrix

Frozen:

- specs/TX-PERTURBATION-MATRIX-v1.json
- docs/MATH-021-CHAPTER-II-TRANSACTION-PERTURBATION-MATRIX.md
- handoffs/B405-CHAPTER-II-PERTURBATION-MATRIX.md

Four causal arms:

### CLEAN x4

Prediction:

VERIFIED -> TARGET_MATCH -> COMMIT.

### RELEASE_ONLY x4

Inject one source-grounded shared-LRU release after VERIFIED.

Prediction:

- release recorded
- expected residual unchanged
- canonical b63 phase preserved
- no INVALIDATE solely because net memory.current falls

### UNEXPECTED_REFILL x4

Force a direct Q64/refill before the frozen target boundary.

Prediction:

INVALIDATED / UNEXPECTED_REFILL.

No TARGET_FAIL.
No COMMIT in the invalidated epoch.

### PTE_GROWTH x4

Deliberately fault an untouched PTE-table region during the verified measured phase.

Prediction:

INVALIDATED / PTE_GROWTH.

Guard precedence overrides an apparent target match.

## Epoch-hazard telemetry

Add to every packet:

- touch_index_since_verified
- elapsed_ns_since_verified
- expected_residual_before
- expected_residual_after
- invalidator type

This creates the first epoch-hazard atlas.

Working model:

hazard is likely event-driven by finite shared structures rather than one homogeneous memoryless failure process.

This is a hypothesis, not yet a result.

## Falsifiers

Chapter II working theory is weakened if complete receipts show:

1. RELEASE_ONLY changes residual phase.
2. CLEAN produces genuine TARGET_FAIL.
3. UNEXPECTED_REFILL can COMMIT in the same epoch.
4. PTE_GROWTH can COMMIT in the contaminated epoch.
5. hard re-prime can use stale receipts.
6. canonical phase changes with no observer-visible invalidator.

Case 6 would imply a missing observer mechanism and is especially important.

## Required order

1. implement native trace/observer wiring
2. run B404 protocol smoke after authorization
3. only if B404 passes, run TX-PERTURBATION-MATRIX-v1
4. then design larger natural epoch-hazard mapping
5. reliability certification remains deferred

## Authority

PAUSE.
No local-PC execution.
No paid runner.
No physical pilot.
No perturbation matrix run.
No large reliability certification.
