# FR-FP-002 Receipt

Status: **PASS / SYNTHETIC SEMANTIC OOM PRESSURE SWEEP QUALIFIED**

Parent: **FR-FP-001**

- workflow run: 37140814727
- job: 111254696934
- execution head: ae1e78259b2cb6bf7cb26423c973962f444f5c3e
- seed: 20261004
- episodes: 1,000
- steps per trajectory: 14
- hot-state budgets: 2 / 4 / 8 / 16

Frozen controls:

- contraction;
- slow drift;
- false-small-residual then jump;
- oscillatory convergence.

Key synthetic findings:

1. RESIDUAL_ONLY at budget 16:
   - semantic corruption rate: about 0.405
   - pressure is absent, so this isolates residual insufficiency.

2. VALIDATED_ENDPOINT at budget 16:
   - semantic corruption rate: 0.0.

3. VALIDATED_ENDPOINT at budget 8:
   - semantic OOM rate: about 0.551.
   - the policy refuses unsafe discard and therefore fails closed under pressure.

4. COLD_TIER_VALIDATED at budget 4:
   - semantic survival rate: 1.0
   - semantic OOM rate: 0.0
   - semantic corruption rate: 0.0
   - mean cold writes: about 5.554 state units.

Interpretation:

A small residual is not sufficient reclaim permission.

Endpoint validation can eliminate premature-discard corruption but exposes a
new failure class: the system may exceed its hot budget before safe
reclaimability arrives.

A cold tier can bridge that interval in the frozen synthetic model by trading
I/O / slower-tier occupancy for semantic survival.

This is a semantic-liveness model, not evidence that any specific Linux, SSD,
KV-cache, or model workload improves in practice.

Decision:

**SEMANTIC_OOM_IS_A_SEPARATE_FAIL_CLOSED_RESEARCH_TARGET**

Next target:

Predict time-to-reclaimability early enough to move live history to a cold tier
before the hot budget is exhausted.

Claim ceiling:

**SYNTHETIC_TRAJECTORY_RECLAIMABILITY_AND_SEMANTIC_OOM_ONLY**
