# MATH-001 Model Competition Result v1

> **Status:** PASS / MODEL64_WINS
> **Run:** `36453581737`
> **Launch commit:** `8ba7be304522c2a2653b99e858b5e7671281d071`
> **Artifact id:** `10985250293`
> **Artifact digest:** `sha256:62d788f0ccc9aa83fdb29f129a709b477357384d679b1026fedb28c3c572e828`

## Decision

`MODEL64_WINS`

Q candidates:

`1,2,4,8,16,32,64,128 pages`

Q=64 is the only candidate that wins all preregistered primary criteria.

## Reset-aware full-sequence residual

Total touch SSE:

| Q pages | reset-aware SSE |
| ---: | ---: |
| 1 | 395648 |
| 2 | 391936 |
| 4 | 387584 |
| 8 | 388096 |
| 16 | 409600 |
| 32 | 512000 |
| **64** | **0** |
| 128 | 2138112 |

Q64 exactly reconstructs all reset-delimited touch regimes.

## Combinatorial MDL

Total position-code length:

| Q pages | MDL bits |
| ---: | ---: |
| 1 | 113.544 |
| 2 | 1006.694 |
| 4 | 792.974 |
| 8 | 504.589 |
| 16 | 280.721 |
| 32 | 133.187 |
| **64** | **30.000** |
| 128 | 93.784 |

Thus divisor aliases are strongly penalized by their false predicted jump positions.

For a clean 4-jump / 256-step block:

- arbitrary four positions: 27.381 bits
- one Q64 phase: 6 bits

This is a 21.381-bit description-length advantage for the exact periodic model before broader model-ID constants.

## Leave-one-block-out prediction

Every fold trained to Q64.

| held-out block | precision | recall | F1 |
| ---: | ---: | ---: | ---: |
| 0 | 1.0 | 1.0 | 1.0 |
| 1 | 1.0 | 1.0 | 1.0 |
| 2 | 1.0 | 1.0 | 1.0 |
| 3 | 1.0 | 1.0 | 1.0 |

Block2 remains perfectly predicted when its observed negative discontinuity defines a reset boundary and phase is recalibrated from the first positive jump of each regime.

Aggregate predictive F1 by Q:

- Q1: 0.0272
- Q2: 0.0538
- Q4: 0.1057
- Q8: 0.2034
- Q16: 0.3810
- Q32: 0.6667
- **Q64: 1.0000**
- Q128: 0.5000

## Control result

No-touch controls contained zero positive events.

No competing periodic pattern was observed in controls.

## Combinatorial sanity check

Under the narrow conditional null where four event positions are sampled uniformly from 256 positions, the probability that they form one exact Q64 arithmetic progression is:

`64 / C(256,4) = 3.661481398759124e-07`

This is only a structural sanity check and is not a causal real-world p-value.

## Interpretation

The hosted evidence has progressed from pattern recognition to predictive model selection.

The result supports:

- a 64-page positive accounting quantum;
- exact 64-page within-regime spacing;
- resettable phase;
- cross-block predictive portability on the tested hosted substrate.

The strongest current model is therefore:

**a resettable Q64 accounting staircase with hidden state controlling phase.**

## Kernel-mechanism consistency

In the inspected upstream Linux source snapshot:

`torvalds/linux@72d3fcf802c45d00b300f25b848a93c3a2bd7c7e`

the memcg charge stock is declared with:

`DEFINE_PER_CPU_ALIGNED(struct memcg_stock_pcp, memcg_stock)`

and accessed through:

`this_cpu_ptr(&memcg_stock)`

The same source defines:

`MEMCG_CHARGE_BATCH = 64U`

This makes CPU identity a direct mechanistic intervention target.

It does not yet prove that CPU migration causes the observed phase reset.

## Next causal question

If phase reflects per-CPU charge-stock state, deliberate CPU migration within the same cgroup should perturb phase/state while preserving the 64-page quantum.

That hypothesis is assigned to MEMCG-002.

## Authority boundary

Hosted research only.
No local-PC execution.
No memory-control policy.
