# FR-FP-006 Receipt

Status: **PASS / SYNTHETIC CAPABILITY REPAIR FRONTIER QUALIFIED**

Parent: **FR-FP-005**

- workflow run: 37143257589
- job: 111261889768
- execution head: b103f70b8470c298db04e06cc105eea90e8d329f

Baseline:
- transfer lead: 4 steps
- hot budget: 4 states
- classification: TRANSFER_SURFACE_CAPABILITY_GAP

Measured repair coordinates:

1. Transfer lead
   - 4 -> 3 steps
   - one-step / 25% lead reduction
   - escapes the capability gap.

2. Hot capacity
   - 4 -> 6 states
   - +2 states / +50% capacity
   - escapes the capability gap.

3. State-size geometry at fixed hot bytes
   - effective state budget 4 -> 6
   - state size must be <= 4/6 of baseline
   - minimum geometric state-size reduction: 33.33%
   - this is not evidence that a physical codec can achieve it.

4. Reclaimability timing
   - current phase map does not identify the required timing shift
   - classification: MODEL_GAP
   - UNKNOWN is not zero.

Cross-lever ranking is forbidden until a common cost model is frozen.

Decision:

**DECOMPOSE_CAPABILITY_GAP_INTO_MINIMAL_MEASURED_REPAIRS_AND_EXPLICIT_MODEL_GAPS**

Claim ceiling:

**SYNTHETIC_CAPABILITY_REPAIR_FRONTIER_AND_GEOMETRIC_EQUIVALENCE_ONLY**
