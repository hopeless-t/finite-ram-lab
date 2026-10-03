# FR-FP-008 Receipt

Status: **PASS / SYNTHETIC COVERAGE-TIMING INTERACTION FRONTIER QUALIFIED**

Parent: **FR-FP-007**

- workflow run: 37143598243
- job: 111262927294
- execution head: f08c7322e131f67426d043c995a6fa2de8a452a6
- baseline transfer lead: 4
- baseline hot budget: 4

Critical frozen cells:

Timing-only repair:
- quality scale: 1.00
- safe shift: 10
- semantic OOM: 19.4%
- reaches the never-safe coverage floor but cannot cross it.

Coverage-only repair:
- quality scale: 0.16
- safe shift: 0
- safe-endpoint coverage: 100%
- semantic OOM remains above 30%.

Joint repair:
- quality scale: 0.16
- safe shift: 8
- safe-endpoint coverage: 100%
- semantic OOM: 0%.

Interpretation:

Coverage and timing are both necessary state variables in the frozen
lead4/budget4 geometry.

A system can make every trajectory eventually reclaimable and still miss the
deadline.

A scheduler can make existing safe events arrive earlier and still fail on
never-safe trajectories.

Decision:

**MODEL_RECLAIMABILITY_AS_JOINT_COVERAGE_AND_TIMING_NOT_ETA_ALONE**

Next:

Replace the two manually separate quantities with a censored time-to-event /
survival formulation and test whether an analytic semantic-OOM law exactly
matches the simulator.

Claim ceiling:

**SYNTHETIC_COVERAGE_TIMING_INTERACTION_ONLY**
