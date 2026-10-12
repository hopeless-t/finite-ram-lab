# Reverse Semantic Forge LLM Lab

Status: ACTIVE / physical evidence exists. No training claim is made for FR-DECIDER or the new LLM lane.

North Star: preserve the minimum sufficient semantic behavior for owner workloads while deleting or externalizing capabilities that do not need to live in model weights.

## Guardrails

- Intent != Authority.
- Protected authority decisions remain outside model weights.
- Training starts only after deterministic, conventional-classifier, and pretrained baselines are measured.
- Failure cases are retained as failure-biopsy evidence.
- Compare total system cost, not parameter count alone.

## Recovered control

The closed/unmerged FR-DECIDER-001 branch was recovered under `legacy/fr-decider-001/`. It remains a System-1/calibration control. No prior physical training or published weights are assumed.

## Corpora

- `corpus/owner-workload-v0.jsonl`: 80 construction tasks, 10 per routing class.
- `corpus/owner-workload-holdout-v1.jsonl`: 40 unseen paraphrases, five per class. The hand-written 0B rules were frozen before this set was evaluated.
- `corpus/ordinary-v0.jsonl`: 12 ordinary Japanese questions for product-surface usefulness.

The first lexical router scored 0.975 on the construction set but only 0.125 on holdout. The construction result is therefore treated as overfit evidence, not generalization quality.

## Evaluator failure biopsy

Evaluator v1 rendered a chat template and then added special tokens again during batch tokenization. Its model-quality results are invalid and are listed in `results/INVALIDATED.md`. Evaluator v2 uses `add_special_tokens=False` for already-rendered chat templates.

## Hardware/runtime

See `manifests/environment-v0.json`.

GAYA-CENTRAL is an Intel Core i3-10110U / AVX2 machine without native BF16 instruction support. A representative SmolLM2-135M forward was about 191.5 ms in FP32 versus 774.4 ms in BF16, so lower storage precision is not assumed to mean lower inference cost on this host.

Qwen3.5 also fell back to correct but slow reference PyTorch implementations for causal-conv and gated-delta kernels because optional optimized kernels were absent. That runtime escape is part of total-system cost.

## Valid routing holdout results

| candidate | state | params / bytes | accuracy | Brier | ECE | median latency | peak RSS |
|---|---|---:|---:|---:|---:|---:|---:|
| lexical rules | frozen holdout | 0 model params | 0.125 | 0.13895 | 0.455 | ~0.018 ms | ~65 MB |
| SmolLM2-135M-Instruct FP32 | pretrained | 134,515,008 | 0.125 | 0.15311 | 0.553 | ~659 ms | ~2.49 GB |
| SmolLM2-360M-Instruct FP32 | pretrained | 361,821,120 | 0.125 | 0.16665 | 0.630 | ~1863 ms | ~2.79 GB |
| Qwen2.5-0.5B-Instruct FP32 | pretrained | 494,032,768 | 0.225 | 0.12267 | 0.240 | ~1379 ms | ~3.47 GB |
| Qwen3.5-0.8B FP32 | pretrained | 852,985,920 physical params | 0.275 | 0.10316 | 0.121 | ~2491 ms | ~6.50 GB |
| char n-gram NB | trained on 80 construction rows | 82,914 bytes | 0.325 | 0.14511 | 0.581 | ~0.164 ms | ~68 MB |
| char n-gram NB + temperature | 64 train + 16 calibration | 67,581 bytes | 0.300 | 0.10001 | 0.196 | ~0.221 ms | ~19 MB |

The tiny conventional classifier currently beats both local Qwen checkpoints in raw routing accuracy by a very large cost margin. Its confidence is not yet trustworthy enough for broad autonomous acceptance: at confidence >= 0.4 it covers 25% of holdout at 50% selective accuracy; confidence >= 0.5 accepts only 1/40 rows (that one is correct). This is a useful FR-DECIDER-style System-1 candidate, not a deployable authority mechanism.

FunctionGemma 270M is Hugging Face manual-gated and no HF credential is configured on this machine. The physical access failure is recorded; the lane remains NOT OBSERVED rather than being scored as a model failure.

## Lesion / externalization experiment

Authority, deterministic mechanics, local-harness mechanics, and retrieval were removed from model responsibility. The residual model task had only four classes: tiny semantic projection, complex reasoning, UNKNOWN, and ordinary conversation.

- Qwen2.5-0.5B: 0.30 accuracy on 20 holdout rows; random floor 0.25.
- Qwen3.5-0.8B: 0.25; exactly random floor.
- Qwen2.5-0.5B with four few-shot examples: 0.25.

Therefore merely deleting externalizable responsibilities or adding a few prompt demonstrations does not recover the owner-specific semantic boundary. A task-specific learned projection is now justified; general-capability training is not.

## Ordinaryness

Qwen2.5-0.5B-Instruct failed the first 12-question ordinary Japanese surface test: concept score 0.25 and fully-satisfied rate 0.0. Observed answers included incorrect expansions such as treating LLM as a legal-office term and RAM as a remote adapter. This checkpoint is not an ordinary-useful local assistant on this host/workload even before owner-DSL routing is considered.

Qwen3.5-0.8B improved to concept score 0.4167 and fully-satisfied rate 0.1667, but required about 149.7 seconds of generation wall time for 12 questions and about 5.75 GB peak RSS. It is better than the 0.5B lane but still fails the ordinary-usefulness gate on this workload.

## Current interpretation

The first Pareto move is not `0.5B -> 0.8B`. It is `general LLM routing -> tiny specialized calibrated System-1 + escalation`.

The remaining research question is whether a very small learned semantic projection can improve generalization and UNKNOWN calibration while leaving arithmetic, retrieval, tool syntax, filesystem mechanics, authority, and long-horizon work outside the model.

## Next physical experiment

1. Keep holdout-v1 sealed from training/tuning.
2. Create a new development corpus with paraphrase diversity and provenance.
3. Train only routing/semantic-projection + UNKNOWN calibration, beginning below the 0.5B lane rather than adding general knowledge.
4. Compare against the 67.6 KB calibrated classifier, not only against larger LLMs.
5. Preserve ordinary user experience through escalation until a local tiny model actually passes the ordinaryness gate.
