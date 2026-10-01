# B480 — Baseline Normalization Decomposition Receipt

Status: **PASS / NORMALIZED EFFECT REPLICATED, COMPONENT UNRESOLVED**

## Frozen execution

- workflow run: 36937797467
- aggregate job: 110622236430
- execution head: 0a02e9ddf0bb40c53773dadd353c67a9ce1b844d
- targeted tests: 3/3 PASS
- runner blocks: 8
- child observations: 64
- aggregate artifact ID: 11198677989
- artifact ZIP SHA256: 420a5bb640b520499b1df073a15d59de74d9070646dfd3d364e120ffb426123d
- aggregate JSON SHA256: 1272235cb678e43ecc0a505c4b444f189470f7345e7af6d834e46fc18def972f

## q2

Seed476 - seed474 block medians:

- normalized peak delta median = **-128,000 B**
- baseline VmHWM delta median = -17,408 B
- absolute work VmHWM delta median = -130,048 B

Block sign tests:

- normalized negative = 8/8, p=0.00390625, significant
- baseline two-sided = p=0.7265625, not significant
- absolute work two-sided = 7 negative / 1 positive, p=0.0703125, not significant

Classification:

**NORMALIZED_EFFECT_COMPONENT_UNRESOLVED**

## q4

Seed476 - seed474 block medians:

- normalized peak delta median = **-105,472 B**
- baseline VmHWM delta median = +38,912 B
- absolute work VmHWM delta median = -78,848 B

Block sign tests:

- normalized negative = 8/8, p=0.00390625, significant
- baseline two-sided = p=0.2890625, not significant
- absolute work two-sided = p=0.2890625, not significant

Classification:

**NORMALIZED_EFFECT_COMPONENT_UNRESOLVED**

## Identity check

For every runner block and q:

`normalized_delta = absolute_work_delta - baseline_delta`

at the block-median summary level.

Maximum absolute identity residual:

`0 B`

The instrumentation is internally consistent.

## Interpretation

B480 rejects the simple explanation:

> the replicated seed effect is merely a stable seed-dependent baseline-HWM shift.

Baseline direction is not consistent across runner blocks.

However B480 also does not yet establish:

> seed changes the absolute work-phase process high-water mark.

The absolute work peak tends downward, especially for q2, but the frozen
familywise two-sided tests do not resolve it.

The robust current fact is narrower:

> the post-input normalized work-growth endpoint is seed-sensitive.

That is not yet enough evidence to make workload seed a physical resource feature
in Governor v1.

## Why another phase split is needed

The current baseline is measured after input generation.

The next measurement should freeze three HWM checkpoints:

1. pre-input process HWM;
2. post-input HWM;
3. post-work absolute HWM.

Then derive separately:

- input-generation HWM growth;
- work growth above post-input baseline;
- total HWM growth from pre-input start;
- absolute post-work HWM.

This can reveal whether the seed sensitivity originates during input preparation,
during the numerical work, or from interactions between both HWM phases.

## Claim ceiling

**GITHUB_HOSTED_BLOCK_NORMALIZATION_DECOMPOSITION**

## Next

B481 should implement the three-phase HWM decomposition on the same q2/q4 x
seed474/476 runner-block design.

Do not update the production Governor with a workload-seed feature until the
physical phase responsible for the seed effect is resolved.
