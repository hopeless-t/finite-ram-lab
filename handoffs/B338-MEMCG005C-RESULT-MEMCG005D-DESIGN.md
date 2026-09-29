# Bounce Handoff

> **Bounce ID:** B338
> **Status:** MEMCG-005C CANONICALIZED / MEMCG-005D DESIGN FROZEN

MEMCG-005C run:
`36551226475`

Decision:
`REJECT_ATOMIC_PATH`

Results:
- ATOMIC: 69/92 Q64, 23 zero-delta failures
- TWO_STEP: 77/92 Q64, 15 zero-delta failures
- ATOMIC worse in 4/4 blocks
- perfect ATOMIC blocks: 0
- ATOMIC 95% Clopper-Pearson: [0.6488574655, 0.8344515379]

Receipt-I/O hypothesis rejected.

MEMCG-005D frozen:
compare SELF_ATOMIC against EXTERNAL_ATOMIC using a prefaulted shared-memory latch and controller-driven sched_setaffinity(pid,S).

Next:
implement only; do not launch during implementation.

Hosted research only.
