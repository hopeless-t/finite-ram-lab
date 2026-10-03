# FR-FP-004 Receipt

Status: **PASS / SYNTHETIC PREDICTIVE RESIDENCY PHASE MAP QUALIFIED**

Parent: **FR-FP-003**

- workflow run: 37141330845
- job: 111256219802
- execution head: a2e7ba37e0836426a7dd9ea4876520f08165e393
- trajectories: 1,000
- transfer leads: 1 / 2 / 3 / 4
- hot budgets: 4 / 6 / 8 / 10
- prediction margins: -1 / 0 / 1 / 2 / 3 / 4

Qualified phase findings:

1. lead=4, budget=4:
   - phase: DEADLINE_INFEASIBLE
   - even ALWAYS_PREEMPTIVE has >99% semantic OOM
   - policy search cannot repair the current transfer geometry.

2. lead=2, budget=8:
   - phase: PREDICTION_SAVES_IO
   - a zero-OOM predictive candidate exists
   - cold-write saving versus always-preemptive exceeds 40%.

3. lead=2:
   - predictive I/O saving increases monotonically as budget slack grows from
     4 -> 6 -> 8 -> 10.

4. lead=3, budget=4:
   - phase: PREDICTION_HAS_NO_MATERIAL_IO_ADVANTAGE
   - predictive zero-OOM behavior exists, but the selective I/O benefit is
     effectively exhausted.

Interpretation:

The Governor now has a feasibility frontier, not only a policy frontier.

In the feasible region, better timing can reduce cold-tier work.

Near the boundary, predictive behavior converges toward preemptive transfer.

Beyond the deadline frontier, no policy optimization can compensate for the
current hot budget / transfer lead combination; the capability surface itself
must change.

Decision:

**DISTINGUISH_POLICY_VALUE_FROM_DEADLINE_FEASIBILITY**

Next:

Compile the phase map into a feasibility oracle that routes each cell to
policy optimization, simple-policy sufficiency, predictor-model gap, or
transfer-surface capability gap.

Claim ceiling:

**SYNTHETIC_PREDICTIVE_RESIDENCY_PHASE_BOUNDARY_ONLY**
