# B481 — Three-Phase HWM Decomposition v0.1

Status: **PRE-INPUT / POST-INPUT / POST-WORK DECOMPOSITION**.

## 1. Question

B480 established a robust seed effect in:

`work VmHWM - post-input VmHWM`

but did not resolve whether the effect belongs to the absolute work peak or the
baseline subtraction.

B481 moves the measurement origin earlier.

## 2. Three HWM checkpoints

Every fresh child records:

1. **pre-input HWM** after interpreter/import setup and GC;
2. **post-input HWM** after deterministic input generation;
3. **post-work HWM** after residue production + grouped CRT reconstruction.

Derived quantities:

```text
input_growth = post_input - pre_input

work_growth = post_work - post_input

total_growth = post_work - pre_input
```

and the hard identity:

```text
total_growth = input_growth + work_growth
```

must hold exactly.

## 3. Why total growth matters

Absolute process HWM contains runtime/interpreter/runner-instance state.

Post-input normalized work growth can inherit properties of the chosen baseline.

Total growth from a pre-input process checkpoint asks a cleaner application
question:

> How much additional high-water memory did this workload require after the
> runtime had started but before workload-specific input preparation?

If this quantity is seed-sensitive across runner blocks, workload identity is a
stronger candidate for the physical resource model.

## 4. Physical design

Eight independent GitHub-hosted job blocks.

Each block runs:

- q2 seed474 x2
- q2 seed476 x2
- q4 seed474 x2
- q4 seed476 x2

with order + reverse order.

Total:

`64 fresh child processes`.

## 5. Confirmatory tests

Six predeclared block-level sign tests:

- q2 input-growth difference, two-sided;
- q2 work-growth seed476<474;
- q2 total-growth seed476<474;
- q4 input-growth difference, two-sided;
- q4 work-growth seed476<474;
- q4 total-growth seed476<474.

The negative work/total directions are frozen from the B479/B480 evidence and are
tested only on the new B481 runner blocks.

Familywise alpha is 0.05 using Holm step-down correction.

## 6. Interpretation

### WORK_PHASE_TOTAL_EFFECT

The post-input work increment and the pre-input-to-work total growth both
replicate, without an input-phase effect.

This supports a workload-sensitive incremental resource requirement.

### INPUT_PHASE_TOTAL_EFFECT

Input preparation and total growth replicate.

### MIXED_PHASE_TOTAL_EFFECT

Both input and work phases contribute.

### POST_INPUT_INCREMENT_ONLY

The old normalized endpoint replicates but total growth does not.

In that case the Governor must not treat seed as a stable total physical
resource feature.

## 7. Governor gate

B481 emits:

`governor_seed_feature_allowed`.

It becomes true only when **both q2 and q4** show a replicated total-growth effect
under one of the total-effect classifications.

This is deliberately conservative.

## 8. Claim ceiling

**GITHUB_HOSTED_THREE_PHASE_HWM_DECOMPOSITION**

## 9. Next

If the Governor gate opens, B482 should build a workload-conditioned calibration
surface using a workload fingerprint rather than the literal random seed.

If the gate remains closed, B482 should revise the primary physical endpoint and
avoid seed-conditioned resource decisions.
