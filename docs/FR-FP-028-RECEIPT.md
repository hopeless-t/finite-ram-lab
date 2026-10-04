# FR-FP-028 Receipt

Status: **PASS / SYNTHETIC REUSE-EVIDENCE STALENESS NEGATIVE RESULT QUALIFIED**

Parent: **FR-FP-027**

- workflow run: 37193140936
- job: 111409371863
- execution head: 544ea0b8e4b7472e8c936e5a6b9a6c59dddcd6c2
- replicates: 5,000
- reuse ceiling: 0.10
- confidence: 95%
- pre-change reuse probability: 0.02
- rolling window: 35

Injected drifts:

p: 0.02 -> 0.15
- cumulative median invalidation delay: 15 observations
- rolling median invalidation delay: 5
- cumulative not invalidated within 60 post-change observations: 7.77%
- rolling not invalidated: 0%

p: 0.02 -> 0.25
- cumulative median delay: 9
- rolling median delay: 3

p: 0.02 -> 0.50
- cumulative median delay: 5
- rolling median delay: 2

Stable low-reuse control (p=0.02 throughout):

- cumulative qualification rate at observation 60: 65.68%
- cumulative conditional false revocation in next 60 observations: 2.07%

- rolling qualification rate at observation 60: 49.42%
- rolling conditional false revocation in next 60 observations: 69.57%

Theory update:

Cumulative evidence can become stale after workload drift.

A fixed rolling exact UCB invalidates much faster, but it also revokes a stable
qualification far too often in this fixture.

Decision:

**REJECT_NAIVE_ROLLING_WINDOW_UCB_AS_THE_DEFAULT_DRIFT_REPAIR**

Next:

Construct an explicit drift-alarm frontier that exposes false-revocation cost
and detection speed separately instead of hiding them behind one fixed rolling
window.

Claim ceiling:

**SYNTHETIC_BERNOULLI_DRIFT_INJECTION_FOR_ONE_10PCT_REUSE_CEILING_ONLY**
