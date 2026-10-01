# B481 — Three-Phase HWM Decomposition Receipt

Status: **PASS / q2 WORK-PHASE TOTAL EFFECT RESOLVED**

## Frozen execution

- workflow run: 36938559927
- aggregate job: 110624657711
- execution head: f637f265071cdfacc24bc35ac0c63feb716a4e38
- tests: 4/4 PASS
- runner blocks: 8
- child observations: 64
- aggregate artifact ID: 11199096801
- artifact ZIP SHA256: 44a0a173e6eaacf56f5901a4877cc967286b0865c53a065da081f688db1b7b43
- aggregate JSON SHA256: 056db37ecc317fedc9ac772767250ccba5d55b726f1715b9ba21ec864e816039

## q2 three-phase result

Seed476 - seed474 median block deltas:

- input-generation HWM growth: -11,264 B
- post-input work HWM growth: **-161,792 B**
- pre-input -> work total HWM growth: **-177,152 B**
- absolute work HWM: -199,680 B

Holm-familywise tests:

- input phase: p=0.2891, not significant
- work phase negative: 8/8, p=0.00390625, significant
- total growth negative: 8/8, p=0.00390625, significant

Classification:

**WORK_PHASE_TOTAL_EFFECT**

This independently strengthens the q2 result beyond the original post-input
normalization endpoint.

## q4 three-phase result

Median deltas:

- input-generation growth: -3,072 B
- work growth: -112,640 B
- total growth: -121,856 B
- absolute work HWM: -126,976 B

Signs:

- work negative 7/8, p=0.03515625
- total negative 7/8, p=0.03515625

These do not survive the frozen Holm familywise procedure.

Classification:

**NO_PHASE_EFFECT_RESOLVED**

## Instrumentation identity

Every block satisfies:

`total_growth = input_growth + work_growth`

Maximum block-summary residual:

`0 B`

## Governor gate

`governor_seed_feature_allowed = false`

The gate requires both q2 and q4 to establish a total-growth effect.

This is intentionally stricter than the q2-only scientific result.

## Scientific interpretation

For q2, the workload-seed effect cannot be dismissed as a stable post-input
baseline artifact.

It reaches the incremental process high-water memory required from before input
materialization through the numerical work phase.

However the literal random seed is still not a meaningful production workload
feature.

A stronger next question is whether the effect follows **input content** when RNG
generation history is removed.

## Next

B482 should pre-materialize the seed474 and seed476 input vectors outside the
measured child process, then load equal-size raw inputs through one identical
loader.

If q2 still shows the work/total effect, the evidence points toward
content-sensitive execution behavior.

If the effect collapses, the earlier seed signal was tied to input-generation or
process-history semantics rather than the numerical content itself.
