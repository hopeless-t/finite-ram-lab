# FR-DECIDER-001 — Sub-1B calibrated decision model

Status: proposed / executable scaffold

## Question

Can the Strands Decider v19 method be pushed below 1B parameters while retaining useful
one-pass routing/calibration quality under a finite-RAM budget?

This lane treats the upstream model as a method, not as a checkpoint to compress.

Reference implementation:
- repository: `strands-labs/strands-decider`
- pinned commit: `890947e7ccd44c3de4115e26a7f46cc5c3147b44`
- license: Apache-2.0
- reference recipe: Qwen3.5-2B-Base + rank-16 LoRA + pointer head

## Two-stage experiment

### A. Same-family downscale: 0.8B

Base: `Qwen/Qwen3.5-0.8B-Base`.

Purpose: isolate parameter-scale effects while keeping the Qwen3.5 family and hybrid
architecture as close to the 2B reference as possible.

### B. True kitten target: 0.5B

Base: `Qwen/Qwen2.5-0.5B` (0.49B).

Purpose: test whether the pointer-head + LoRA decision recipe survives a cross-generation
torso change while cutting resident weight memory substantially.

This is an independent derived model. It must not be presented as an official Strands
checkpoint.

## Frozen invariants

Both lanes keep, unless a preregistered ablation changes them:

- pointer head;
- pointer_dim = 256;
- LoRA rank = 16, alpha = 32;
- shuffled options;
- one training epoch;
- gradient checkpointing;
- identical training/evaluation rows;
- per-primitive post-hoc calibration;
- JevBench public task IDs fixed for cross-model comparison.

The first 0.8B and 0.5B runs change only the torso and resource-sensitive batch settings.

## Measurements

Record for every candidate:

- JevBench public accuracy and attempted-task count;
- Brier score;
- ECE;
- easy / standard / hard accuracy;
- median and p95 latency for fixed request shapes;
- process peak RSS;
- accelerator peak allocation when available;
- checkpoint bytes;
- base-weight bytes;
- cold-load wall time;
- train wall time;
- calibration split identity;
- exact upstream commit and base-model revision.

Do not use leaderboard rank as the optimization objective.

## Finite-RAM objective

Let

- A = accuracy,
- B = Brier score,
- E = ECE,
- L = p95 latency,
- R = peak resident bytes.

A candidate x Pareto-dominates y only when it is no worse in all measured objectives
and strictly better in at least one:

`A_x >= A_y, B_x <= B_y, E_x <= E_y, L_x <= L_y, R_x <= R_y`.

The experiment reports the frontier rather than collapsing these quantities into one
arbitrary weighted score.

## Primary hypotheses

H1: the 0.8B model retains most easy/standard classification quality while reducing
resident memory enough to move the local Pareto frontier.

H2: the 0.5B model loses more hard-tier capability than the 0.8B model, but can still
be useful as a high-confidence first-stage router if calibration remains honest.

H3: confidence-gated escalation can make the 0.5B model operationally useful even when
its unconditional accuracy is below the 2B reference.

## Escalation experiment

For confidence threshold t, measure:

- coverage(t): fraction accepted by the kitten;
- selective_accuracy(t): accuracy among accepted rows;
- escalation_rate(t) = 1 - coverage(t);
- expected decision cost under a fixed stronger-model fallback.

Do not choose t on JevBench test rows. Fit it on a separate validation split.

## Resource protocol

The local machine is the target environment; GitHub-hosted Actions are validation only.

Do not train the model in GitHub Actions. Hosted CI may:
- validate configs;
- run synthetic metric aggregation;
- validate result JSON;
- verify pinned references.

Training/evaluation runs must emit immutable result artifacts before interpretation.

## Reproducibility

The first run should use the pinned upstream Strands commit above. If upstream changes,
open a new run generation rather than silently moving the reference.

All Hugging Face publication metadata must include:
- exact base model;
- exact upstream Strands commit;
- license attribution;
- training-data provenance;
- evaluation caveats;
- calibration procedure;
- measured memory/latency hardware.

## Publication gate

A Hugging Face upload is allowed only after:

1. a checkpoint loads from a clean environment;
2. calibration has been run;
3. JevBench public evaluation completes without schema failures;
4. resource measurements are recorded;
5. the model card clearly identifies the model as an independent derivative;
6. no benchmark-private or sealed data are included.

Provisional names:
- `hopeless-t/kitten-decider-0.8b`
- `hopeless-t/kitten-decider-0.5b`

Names are placeholders until publication.
