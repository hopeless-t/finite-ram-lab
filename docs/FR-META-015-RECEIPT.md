# FR-META-015 Receipt

Status: **PASS / FIRST PROSPECTIVE COMPILED-SKILL DOGFOOD**

- workflow run: 37139937386
- job: 111252083102
- execution head: 1ddb87bc683a2c0f70111bfa57308c12b8b2ac56
- qualification artifact ID: 11280405014
- artifact ZIP SHA256: bc3c6ed1c9964dee12238dcc407b0dab2a4978124aac33ee85fba2e14f3a58f8

Decision path:

Facts supplied to FR-META-014:
- deterministic_duplicate_work = true
- scientific_contract_unchanged = true
- runtime_is_measurement = false

Compiled result:
- primary action: REUSE_EXACT_COMPUTATION
- Monte Carlo policy: SKIP
- full-history fallback: not required
- selected decision context: under 5% of the frozen 17,417-character source surface

Scientific guard:

- episodes unchanged: 8,192
- frames per segment unchanged: 120
- observer arms unchanged: 3
- original reference implementation equality checks: PASS
- full pre-existing frozen ABA output gate: PASS

Compute graph:

- B stochastic tape passes: 24,576 -> 8,192
- B tape generation reduction: 66.67%
- segment loops per episode: 5 -> 3
- overall segment-loop reduction: 40%

Observed ABA hot-test completion gap:

- original pre-FR-META-006: 29.091 s
- after first exact memoization: 22.951 s
- after skill-routed common tape: 15.007 s
- reduction versus previous stage: about 34.6%
- reduction versus original specimen: about 48.4%

Decision:

**SHARE_B_STOCHASTIC_TAPE_ACROSS_OBSERVER_ARMS**

This is the first prospective experiment whose routing decision was made by a
compiled decision skill rather than by reconstructing the full FR-META history.

Claim ceiling:

**SKILL_ROUTED_EXACT_TEST_HARNESS_OPTIMIZATION_ONLY**
