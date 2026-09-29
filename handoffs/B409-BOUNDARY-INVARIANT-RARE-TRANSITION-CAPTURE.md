# B409 — Boundary invariant rare-transition capture

## Status

COMPLETE / DESIGN MATH / NO PHYSICAL RUN.

## Core theorem

After a verified direct Q64 primer:

R_0 = 63.

With one clean measured data page consumed per touch and no state-changing event:

R_t = 63 - t

for post-primer touches t=0..63.

Therefore the next direct Q64 boundary is:

T_0 = 64.

## Boundary innovation

Define:

Delta = T - 64.

Interpretation under the simplified one-batch model:

- Delta = 0: canonical
- Delta < 0: early exhaustion / net residual loss
- Delta > 0: delayed exhaustion / net residual gain or missed event

The phase shift itself becomes a quantitative fingerprint.

## Rare specimen

UNEXPLAINED_BOUNDARY_DEVIATION requires:

- verified direct-Q64 start
- complete receipts
- CPU/worker clean
- no PTE growth
- no drain
- no known state-changing antecedent
- owner release absent or fully classified
- T != 64

On capture:

- no same-identity retry
- no commit
- freeze full epoch
- preserve owner counter
- preserve boundary-adjacent trace windows
- reproduce only in a new independent identity

## Key conceptual correction

An unexpected early Q64 is a boundary symptom, not automatically the causal mechanism.

The hunt asks:

> what changed the residual state before the boundary?

## Hazard decomposition

Record both:

- touch age a
- wall-clock age tau

A touch-dependent shift suggests activity-driven stock consumption.

A time-dependent shift at comparable touch age suggests asynchronous control/workqueue/competition paths.

Linux memcg has a drain_all_stock path capable of queuing per-CPU drain work, so wall-clock exposure is mechanistically meaningful.

## Proof boundary

Can prove/model-check:

- protocol safety properties
- stale epoch rejection
- re-prime freshness
- clean 64-boundary theorem conditional on assumptions

Cannot prove from math alone:

- observer completeness in the physical kernel
- absence of all unknown mechanisms

Those require sentinels and physical evidence.

## Artifacts

- specs/TX-BOUNDARY-DEVIATION-HUNT-v1.json
- docs/MATH-022-BOUNDARY-INVARIANT-RARE-TRANSITION-CAPTURE.md

## Next

Successor transactional-spawn runner orchestration becomes the next implementation bounce.

Physical execution remains paused.
