# FR-FP-003 Receipt

Status: **PASS / SYNTHETIC PREDICTIVE COLD-TIER GOVERNOR QUALIFIED**

Parent: **FR-FP-002**

- workflow run: 37141063520
- job: 111255420682
- execution head: 6f360fa60caf707b4094890a9975b50a492afe18
- transfer lead time: 2 steps
- prediction margin: 1 step
- future-trace leakage test: PASS

Frozen budget-8 comparison:

REACTIVE_TRANSFER
- semantic OOM rate: about 0.551

PREDICTIVE_TRANSFER
- semantic OOM rate: 0.0
- mean cold writes: about 3.836 state units

ALWAYS_PREEMPTIVE
- semantic OOM rate: 0.0
- mean cold writes: about 7.360 state units

Thus the predictive arm preserves the frozen semantic-OOM result while using
roughly 47.9% fewer cold writes than always-preemptive at budget 8.

Frozen budget-4 comparison:

PREDICTIVE_TRANSFER
- semantic OOM rate: 0.0
- mean cold writes: about 7.175

ALWAYS_PREEMPTIVE
- mean cold writes: about 7.360

The I/O advantage nearly disappears under the tighter budget.

Interpretation:

Prediction has the most value when the system has enough slack to choose when
to move state.

When slack collapses, the policy converges toward always-preemptive behavior.

Decision:

**ADD_TIME_TO_RECLAIMABILITY_TO_THE_GOVERNOR_STATE**

Next:

Map the phase boundary across hot budget and transfer lead time, including the
region where even always-preemptive transfer cannot meet the deadline.

Claim ceiling:

**SYNTHETIC_PREDICTIVE_TRANSFER_TIMING_ONLY**
