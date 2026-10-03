# FR-FP-018 Receipt

Status: **PASS / ORDER-ONLY MONTE CARLO NULL QUALIFIED**

Parent: **FR-FP-017**

- workflow run: 37153147849
- job: 111290978849
- execution head: d4b4761d679c2ce9a1fe5a52c7108e799d5b9991
- frozen hosted source trace: workflow 37152732983
- shuffles per arm: 20,000
- Bonferroni familywise alpha: 0.05 / 7 = 0.007142857

COLD observed order statistics:
- lag1: -0.240, p(abs) = 0.09010
- lag2: -0.391, p(abs) = 0.00345
- lag4: +0.277, p(abs) = 0.05685
- >25 ms max run: 1
- anti-cluster lower-tail p = 0.2523
- epoch miss-range p = 0.4703
- epoch median-range p = 0.4612

COLD significant after correction:
- lag2 only

WARM control:
- lag1: +0.092, p(abs) = 0.5310
- lag2: -0.473, p(abs) = 0.000650
- lag4: +0.437, p(abs) = 0.002150

WARM significant after correction:
- lag2
- lag4

Routing:

**SHARED_ENVIRONMENT_OR_HARNESS_TEMPORAL_STRUCTURE_CANDIDATE**

Interpretation:

The COLD trace contains a statistically unusual lag-2 ordering relative to its
own shuffled marginal distribution.

However, the WARM control contains even stronger corrected lag-2 / lag-4 order
effects.

Therefore this single trace does not support attributing the order effect to a
COLD-only latent I/O state.

The much larger COLD tail and cross-run nonstationarity remain real, but the next
model should first expose shared runner / I/O pressure observables rather than
jump directly to a COLD-only HMM.

Meta-failure closed during qualification:

A downstream CI failure exposed that FR-FP-016 still required monotonic COLD
size scaling even after its negative result had rejected that shape. The
negative-result CI contract was repaired and restacked before final
qualification.

Decision:

**OBSERVE_SYSTEM_IO_STATE_AROUND_COLD_RESTORE_BEFORE_FITTING_A_COLD_ONLY_LATENT_STATE_MODEL**

Claim ceiling:

**ORDER_STRUCTURE_TEST_ON_ONE_FROZEN_48_SAMPLE_HOSTED_TRACE_ONLY**
