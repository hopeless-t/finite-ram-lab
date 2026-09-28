# MEMCG-003 Canonical Result — B306

Canonical run: `36459951576`
Launch head: `6cb688d7c8578ce95e217e83adcb7249a3555efa`
Aggregate artifact: `MEMCG-003-SEVEN-SLOT-36459951576`

## Preregistered decision

`REJECT_K7_SLOT_MODEL`

- support blocks: 0/4
- observed first-event thresholds: [2, 1, 4, 2]
- modal / median threshold: 2 / 2.0
- best K by absolute error: 2
- Bayesian posterior mode: K=2, posterior 0.88545
- K=7 posterior: 2.14e-7
- LOBO trained K: 2 in all four folds

## Critical control finding

The apparent K=2 result is **not accepted as a replacement cache-capacity law**.

Every control family produced Q64-sized events:
- same-memcg: 1 event in every block
- no-churn: 1,1,2,1 events
- six-only: 2,1,2,3 events

Therefore challenger count is not sufficient to explain the first-event statistic.

The target probe itself advances the target's 64-page charge phase. A later probe can cross a Q64 boundary even without distinct-memcg churn. This aliases phase crossing with eviction.

## Council convergence

1. Primary preregistered K7 model: REJECT.
2. Post-hoc K2 cache-capacity interpretation: REJECT as unsupported.
3. Q64 recharge mechanism: retained; fresh Q64 appeared at each distinct first event.
4. Current assay is phase-confounded and cannot identify slot capacity from first-event index.
5. Geometry/MATH-002 cannot rescue the failed primary test. It may only describe the confounded response cloud.
6. Next experiment must observe stock state without consuming target charge phase, or explicitly randomize/match phase.

## OSS-relevant consequence

Before testing DONTNEED cadence or cache occupancy, measurement must separate:
- intervention-driven reclaim/eviction,
- ordinary Q64 charge-phase crossings,
- observer/probe perturbation.

This is directly relevant to finite-RAM tuning: a cadence benchmark that does not phase-match its control can falsely attribute normal batching to reclaim policy.

## Next proposal (not decision)

MEMCG-004 / PHASE-MATCHED NONCONSUMING OBSERVATION:
- freeze target after initial charge where possible;
- read cgroup counters without touching another target page;
- separate intervention actor from measurement actor;
- include no-churn time-matched controls;
- if a consuming probe is unavoidable, randomize initial target phase and subtract matched phase hazard;
- collect memory.current, memory.stat, memory.events, PSI, latency;
- only after measurement hygiene is validated, add DONTNEED cadence arms.

Proposal ≠ Decision.
No local execution.
