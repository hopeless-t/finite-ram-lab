# CURRENT

> Latest bounce: B409
> Stage: CHAPTER II BOUNDARY-INVARIANT RARE-TRANSITION CAPTURE DESIGN
> Stop: PHYSICAL PAUSE / READY FOR SUCCESSOR TRANSACTIONAL-SPAWN RUNNER

## Chapter II objective

Once a direct Q64 reset is verified:

> identify which events preserve the epoch, which destroy it, and capture any phase shift not explained by the known observer.

## Leading mechanistic invariant

Immediately after a verified Q64 primer:

R_0 = 63.

Under a clean uninterrupted epoch:

R_t = 63 - t

for post-primer touches t=0..63.

Therefore the next direct Q64 boundary is:

T_0 = 64.

This is conditional on:

- same intended stock lane
- one fresh data page per measured touch
- no PTE growth
- no drain
- no unexpected state reset
- complete trace
- CPU/worker clean

Positively classified shared-LRU release does not alter residual stock.

## Boundary innovation

Define:

Delta = T - 64.

Under the simplified one-batch model:

- Delta = 0 -> canonical boundary
- Delta < 0 -> early exhaustion / page-equivalent residual loss
- Delta > 0 -> delayed exhaustion / residual addition, omitted consumption, missed observer event, or violated assumption

The boundary shift is a localization fingerprint, not an automatic causal label.

## Chapter II rare pokemon

The high-value specimen is:

UNEXPLAINED_BOUNDARY_DEVIATION

Required:

- direct-Q64 VERIFIED start
- complete epoch-local receipts
- CPU/worker clean
- no PTE growth
- no observed drain
- no known causal state-changing antecedent
- all target-owner release events absent or positively classified
- T != 64

An early Q64 is the symptom.

The research question is:

> what changed residual stock before the boundary?

## Capture action

On an unexplained candidate:

- stop before COMMIT
- no same-identity retry
- freeze complete epoch archive
- freeze owner_counter
- retain boundary-adjacent trace windows
- record Delta
- reproduce only in a new independent identity

Do not dilute a specimen with automatic re-prime.

## Touch age vs wall-clock age

Packet v2 records:

- a = touch_index_since_verified
- tau = elapsed_ns_since_verified

This permits mechanism localization:

- effect follows a -> activity/touch-driven candidate
- effect follows tau at comparable a -> asynchronous/time-driven candidate

Linux memcg has a drain_all_stock path that can queue per-CPU drain work, so wall-clock age is a mechanistically meaningful axis.

## Mathematical proof boundary

### Protocol properties

Can be exhaustively tested/model-checked:

- invalidated epoch cannot COMMIT
- stale epoch receipts are rejected
- re-prime clears observer authority
- fresh Q64 is required after re-prime
- release-only does not decrement residual
- TARGET_MISMATCH is not retried away

### Boundary theorem

Given the clean assumptions:

T_0 = 64

follows by induction from R_0=63 and one-page consumption.

### Physical mechanism

Math alone cannot prove the observer has no blind spot.

A complete unexplained deviation can still represent:

- unknown state-changing mechanism
- observer false negative
- violated model assumption
- undetected instrumentation loss

Physical sentinels and independent reproduction distinguish these.

## B405 perturbation matrix

Frozen causal controls:

- CLEAN x4
- RELEASE_ONLY x4
- UNEXPECTED_REFILL x4
- PTE_GROWTH x4

Run only after B404 protocol smoke.

## B406 observer

Implemented:

- TRANSACTION-RECEIPT-PACKET-v2
- epoch-local owner_counter
- positive source-grounded release classifier
- touch/wall-clock hazard coordinates
- fail-closed unknown emission handling

## B407 archive

Implemented:

- transaction_epoch_archive.py
- re-prime clears owner/hazard state
- stale epoch rejection
- fresh-owner synthetic sentinel replay

Synthetic replay CI passed.

## B408 native marker envelope

Implemented:

- transactional_spawn_native.py
- FRL_TX PRE -> frozen historical _touch() -> FRL_TX POST
- Chapter-I primitive unchanged
- missing window fails closed

No physical workflow or launch marker created.

## B409 artifacts

- specs/TX-BOUNDARY-DEVIATION-HUNT-v1.json
- docs/MATH-022-BOUNDARY-INVARIANT-RARE-TRANSITION-CAPTURE.md
- handoffs/B409-BOUNDARY-INVARIANT-RARE-TRANSITION-CAPTURE.md

## Next

Implement the successor transactional-spawn runner:

1. hard-new-worker epoch lifecycle
2. P-side PTE precondition
3. migration to stock CPU
4. bounded NORMALIZE with direct receipts
5. CONSUME
6. TARGET bundle
7. per-epoch archive persistence
8. boundary T and Delta telemetry
9. no automatic physical launch

Then, after authorization:

B404 smoke -> B405 perturbation matrix -> boundary-deviation hunt.

## Authority

PAUSE.
No local-PC execution.
No paid runner.
No physical pilot.
No perturbation matrix.
No boundary hunt.
No large reliability certification.
