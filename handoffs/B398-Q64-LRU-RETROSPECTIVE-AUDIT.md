# B398 — Q64 / LRU retrospective audit

## Status

RETROSPECTIVE AUDIT COMPLETE / NO NEW PHYSICAL RUN.

Canonical audit:
docs/RETROSPECTIVE-2026-09-30-Q64-LRU-AUDIT.md

## Three-layer model

1. Natural incidence: CAP10+ association survives width control and block conditioning; cause unresolved.
2. Controlled transition: Q64-primer-conditioned b62/b63/b64 arithmetic matches 55/55; frozen strict endpoint remains 49/72.
3. Observation emission: recurrent -17 is shared per-CPU LRU-batch release, constructively reproduced by OBS-005.

## Strong closure

OBS-005:
- 15/15 scrub-success trials show producer exact -17 during trigger phase.
- 12/12 counter-grounded cases show producer page-counter uncharge17.
- canonical producer17 + trigger14 = batch31 constructed.

The dominant -17 lane is sufficiently closed for the Q64 mainline.

## Open

- physical cause of CAP10+ natural incidence
- exact natural initial stock-state distribution
- PTE effect magnitude
- rarer negative deltas -13/-3/-2
- raw-start b63 reliability
- cross-kernel transport

## Documentation correction

The early OBS-002 TRACEFS_HOLD document is now explicitly marked SUPERSEDED by later successful corrected tracefs/kprobe work.

## Next

OBS-006 decontaminated charge-side Q64 observer.

No b63 reliability scaling before OBS-006 validation.