# FR-FP-007 Receipt

Status: **PASS / SYNTHETIC RECLAIMABILITY TIMING-COVERAGE DECOMPOSITION QUALIFIED**

Parent: **FR-FP-006**

- workflow run: 37143412551
- job: 111262365629
- execution head: 00d4b1dc8f3971a4b8410da9b3cb530558214933
- transfer lead: 4 steps
- hot budget: 4 states
- trajectories: 1,000

Safe-reclaimability coverage:

- observed safe endpoint inside horizon: 806 / 1,000
- never-safe trajectories: 194 / 1,000
- coverage: 80.6%
- never-safe fraction: 19.4%

Timing sweep:

- shifting existing safe events earlier reduces semantic OOM monotonically;
- sufficiently large timing shifts drive semantic OOM down to exactly 19.4%;
- further timing improvement cannot cross that floor.

Interpretation:

Two distinct failure domains are present:

TIMING_GAP
- a safe endpoint exists;
- it arrives too late relative to hot-budget slack and transfer lead.

COVERAGE_GAP
- no safe endpoint appears within the observed horizon;
- timing acceleration cannot repair a nonexistent event.

Decision:

**SEPARATE_RECLAIMABILITY_TIMING_FROM_RECLAIMABILITY_COVERAGE**

Governor consequence:

A predictive Governor needs not only ETA_reclaimable but also a calibrated
reclaimability-coverage / probability signal.

Claim ceiling:

**SYNTHETIC_RECLAIMABILITY_TIMING_AND_COVERAGE_DECOMPOSITION_ONLY**
