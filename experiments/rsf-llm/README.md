# Reverse Semantic Forge LLM Lab

Status: ACTIVE. Physical pretrained screening **and physical task-specific training are now observed** for the new RSF lane. The recovered historical FR-DECIDER lane still has no observed historical training or published weights.

North Star: preserve the minimum sufficient semantic behavior for owner workloads while deleting or externalizing capabilities that do not need to live in model weights.

## Guardrails

- **Intent != Authority.** Authority is an MVCA/system concern, not a language-model class.
- Protected authority decisions remain outside model weights.
- Failure cases and invalid measurements are retained as failure-biopsy evidence.
- Compare total system cost, not parameter count alone.
- Holdout-v1, holdout-v2, and holdout-v3 are observed/spent benchmarks. Never tune against them; create a new sealed holdout before the next iteration.
- No adapter weights are committed or published. Local checkpoints live under ignored `.work/` only.

## Recovered historical control

The closed/unmerged FR-DECIDER-001 assets are recovered under `legacy/fr-decider-001/`. They remain a System-1/calibration control. Do not infer prior training from those files.

## Corpora

- `corpus/owner-workload-v0.jsonl`: 80 construction tasks, 10 per original routing class.
- `corpus/owner-workload-holdout-v1.jsonl`: 40 unseen paraphrases, five per original class.
- `corpus/ordinary-v0.jsonl`: 12 ordinary Japanese product-surface questions.

The first hand-written 0B router scored 0.975 on construction but only 0.125 on frozen holdout. The 0.975 result is overfit evidence, not generalization quality.

## Evaluator failure biopsy

Evaluator v1 rendered chat-template special tokens and then added special tokens again during batch tokenization. Its model-quality results are retained but listed in `results/INVALIDATED.md`. Evaluator v2 fixes this with `add_special_tokens=False` for already-rendered chat templates.

A later semantic-7 training launcher initially failed with `KeyError: authority` after authority had been removed from the class set but not from the split function. The launcher was repaired to filter authority rows explicitly before training.

## Host/runtime

See `manifests/environment-v0.json`.

GAYA-CENTRAL is an Intel Core i3-10110U / AVX2 machine without native BF16 instruction support. A representative SmolLM2-135M forward was ~191.5 ms FP32 versus ~774.4 ms BF16, so lower storage precision is not assumed to mean lower inference cost on this host.

Qwen3.5 also fell back to correct but slow reference PyTorch implementations for optional causal-conv / gated-delta kernels. Runtime escape is part of total-system cost.

## Pretrained routing holdout

| candidate | params | accuracy | Brier | ECE | median latency | peak RSS |
|---|---:|---:|---:|---:|---:|---:|
| lexical rules | 0 model params | 0.125 | 0.13895 | 0.455 | ~0.018 ms | ~65 MB |
| SmolLM2-135M-Instruct FP32 | 134,515,008 | 0.125 | 0.15311 | 0.553 | ~659 ms | ~2.49 GB |
| **LLM-jp-3-150m-Instruct3 FP32** | 152,318,464 | 0.125 | 0.18400 | 0.697 | ~100 ms | ~1.58 GB |
| SmolLM2-360M-Instruct FP32 | 361,821,120 | 0.125 | 0.16665 | 0.630 | ~1863 ms | ~2.79 GB |
| Qwen2.5-0.5B-Instruct FP32 | 494,032,768 | 0.225 | 0.12267 | 0.240 | ~1379 ms | ~3.47 GB |
| Qwen3.5-0.8B FP32 | 852,985,920 physical params | 0.275 | 0.10316 | 0.121 | ~2491 ms | ~6.50 GB |
| char n-gram NB | 82,914-byte model | 0.325 | 0.14511 | 0.581 | ~0.164 ms | ~68 MB |
| char n-gram NB + temperature | 67,581-byte model | 0.300 | 0.10001 | 0.196 | ~0.221 ms | ~19 MB |

FunctionGemma 270M remains NOT PHYSICALLY OBSERVED because the Hugging Face repository is manual-gated and no HF credential is configured on GAYA-CENTRAL.

## Ordinaryness

- Qwen2.5-0.5B-Instruct: concept score **0.25**, fully-satisfied **0.0**.
- Qwen3.5-0.8B: concept score **0.4167**, fully-satisfied **0.1667**, ~149.7 s generation wall for 12 questions, ~5.75 GB peak RSS.
- LLM-jp-3-150m-Instruct3: concept score **0.1667**, fully-satisfied **0.0**, but much lower local generation cost (~6.77 s wall for 12 questions, ~1.46 GB peak RSS).

None passes the current ordinary-usefulness gate. Ordinary user experience must therefore remain a system-level requirement with escalation, not be falsely claimed from the local tiny model.

## Physical training experiments

All LoRA experiments use pinned `llm-jp/llm-jp-3-150m[-instruct3]`, rank 4, alpha 8, q/v projection targets, and only **98,304 trainable parameters**. The PEFT adapter weight itself is about **399 KB**; the ~6.8 MB local checkpoint bundle is mostly the tokenizer. Adapter binaries are not committed or published.

| experiment | model responsibility | train / cal / holdout | accuracy | Brier | ECE | median latency | peak RSS |
|---|---|---:|---:|---:|---:|---:|---:|
| 8-way LoRA | authority + all semantic routes | 64 / 16 / 40 | **0.45** | 0.09412 | 0.250 | ~111 ms | ~2.06 GB |
| semantic-7 LoRA | authority externalized; all other routes internal | 56 / 14 / 35 | **0.6857** | 0.06127 | 0.130 | ~110 ms | ~1.99 GB |
| residual-4 LoRA | authority + deterministic + harness + retrieval externalized | 32 / 8 / 20 | **0.85** | 0.06493 | 0.139 | ~111 ms | ~1.53 GB |
| residual-4 LoRA from **Base** | same four residual duties; instruction tuning removed | 32 / 8 / 20 | **0.75** | 0.11783 | 0.261 | ~193 ms | ~1.98 GB |

### What the 8-way failure taught us

The 8-way adapter raised holdout accuracy from 0.125 pretrained to 0.45, but all five authority holdout rows were confidently misrouted to `harness`. This was partly amplified by the abstract authority training vectors, but more importantly it exposed a design mistake: **Authority should never have been an LLM route class.** The semantic-7 experiment removes it structurally.

### What responsibility deletion did

With the same 150M substrate and the same 98,304 trainable LoRA parameters:

- pretrained 8-way: **12.5%**
- trained 8-way: **45%**
- trained semantic-7: **68.6%**
- trained residual-4: **85%**

This is the first direct physical evidence in this lab that reducing model responsibility can improve owner-workload semantic fidelity more than increasing the pretrained parameter count from 150M to 500M/800M.

The residual-4 result is **conditional**: it assumes authority/deterministic/harness/retrieval have already been externalized correctly. It is not an end-to-end product score. A 67 KB char-n-gram externalization gate was tested and failed at **25%**, so the externalization mechanism is still unsolved.

The semantic-7 result is the more realistic one-pass semantic result: authority is external by architecture, while deterministic/harness/retrieval/tiny/larger/UNKNOWN/ordinary are still selected by the 150M model. It reaches **68.6%** on 35 holdout rows. At confidence >= 0.8 it covers ~54.3% with ~84.2% selective accuracy; at >= 0.9 it covers 40% with ~85.7% selective accuracy.

## Base-model lesion

Removing instruction tuning entirely did **not** destroy residual-4 capability: LLM-jp-3-150m Base + the same LoRA reached 75%. Instruct3 retained a useful +10 percentage-point advantage (85% vs 75%), so instruction tuning is not pure residue, but most of the task-specific route capability can be rematerialized from the Japanese base model.

## Current Pareto interpretation

The current frontier is no longer `0.5B -> 0.8B`.

It is approximately:

1. tiny deterministic / conventional mechanisms where they are genuinely reliable;
2. **150M Japanese semantic substrate + ~98K trainable projection parameters** for owner-specific intent;
3. explicit confidence-gated escalation;
4. larger/cloud models only for residual work that does not fit the tiny substrate.

The 67 KB classifier remains an important cheap control, but its selective confidence is too weak for broad routing. The 150M residual-4 adapter is much more capable but still too large in RSS to call the final minimum sufficient existence.

## Shoal runtime: first end-to-end externalization prototype

A first physical `ShoalRouter` now combines an external authority policy, 0B lexical/deterministic signals, a lazy-loaded 150M semantic-7 LoRA router, confidence-gated handoff, and explicit specialist targets. This is a system experiment rather than a claim that the 150M model alone is sufficient.

The new semantic-7 adapter was trained only on `owner-workload-dev-v1` (70 train / 14 calibration rows). The first long launcher exceeded the Local MCP 90 s execution budget and is retained as `semantic7-dev-v1-training-timeout.json`; removing redundant per-epoch full-train evaluation allowed a 4-epoch run to complete in **53.2 s**. Calibration accuracy reached **92.9%** with temperature **0.5**, again with only **98,304 trainable parameters**.

### Sealed cascade results

| sealed benchmark | hybrid Shoal | policy + semantic7 only | 150M model-active fraction | note |
|---|---:|---:|---:|---|
| holdout-v2 (48 rows) | **97.9% (47/48)** | 85.4% | **25.0%** | 0B single-signal 30/30; policy guard 6/6 |
| holdout-v3 (48 harder rows) | **91.7% (44/48)** | 81.25% | **35.4%** | 0B single-signal 25/25; direct semantic7 12/12 |

Both holdouts were hash-sealed before the corresponding tuning step and were immediately marked `spent` after their first evaluation. No post-hoc rescoring is allowed. The v3 misses were all boundary-policy failures (`low_confidence_handoff` or `signal_model_conflict`), not direct errors from the accepted 0B or accepted semantic7 routes.

### Lazy activation

The router no longer imports or loads PyTorch/model weights for a request that can be resolved by 0B policy/signals. On GAYA-CENTRAL a deterministic fast-path smoke test completed in about **0.04 s / 16 MB max RSS**. A request requiring the 150M router paid a cold path of about **5.9 s / 1.43 GB max RSS**. The current engineering objective is therefore to increase correct sleeping time, not merely shrink total parameter pool size.

### Practical GAYA workcell

`shoal_workcell.py` is the first executable specialist workcell. It can currently:

- complete safe arithmetic with a 0B AST calculator;
- execute a bounded read-only local Harness subset (`pwd`, `git status`, `HEAD`, `git diff --stat`, branch listing, explicit in-tree file stat);
- never pass natural-language text into a shell; all local commands use fixed argv;
- hand off all unsupported work instead of inventing execution;
- log only trace metadata plus a SHA-256 of the request text to ignored `.work/rsf-llm/runtime-events.jsonl`.

A local convenience entrypoint is installed as `~/.local/bin/catfood-shoal`. Practical smoke tests physically completed `git status`, `pwd`, `git rev-parse HEAD`, `README.md` stat, and arithmetic on GAYA-CENTRAL. Adapter binaries and runtime event logs remain local/ignored.


## Finite-RAM cross-pollination into Shoal runtime

Selected control principles were ported from the latest observed `finite-ram-lab` mainline (`origin/main@2b8f870`) without merging that branch wholesale. The imported atoms are operational, not just documentation:

- **byte-canonical admission:** local semantic-model activation is governed by estimated bytes and live `MemAvailable`, not by model/object counts;
- **memory-pressure hysteresis:** PSI + byte-reserve thresholds use a deadband so borderline pressure does not thrash model activation;
- **durable != resident:** receipts may grow on disk while the controller's resident event state remains byte-bounded;
- **shared-prefix residency:** the 28-token prompt prefix is cached as KV state and reused across semantic-router calls;
- **profile-guided closure:** every optimization keeps the same dev task set and verifies correctness before accepting the resource gain.

Physical observations on GAYA-CENTRAL:

- synthetic governor trace: `NORMAL -> PRESSURE -> hold -> recover` passed for both byte-pressure and PSI arms;
- under forced pressure, the router hands off **without loading the 150M model**;
- 100 durable synthetic receipts grew to 15,980 bytes while the resident control-state file stayed at **353 bytes / 2 compact entries** under a strict 512-byte budget;
- the ordinary runtime uses a 4,096-byte resident control-state budget;
- shared-prefix warm forward median improved from **98.8 ms to 55.2 ms (~1.79x)** over 20 local probes, with max absolute logit difference `4.39e-05`;
- dev-v2 stayed **64/64 correct** while end-to-end wall for the same evaluator moved from **6.589 s to 5.927 s** after prefix reuse.

The current provisional local governor treats the semantic worker as ~1.5 GiB and preserves a 3 GiB enter reserve / 5 GiB recovery reserve, plus PSI hysteresis. These are local policy knobs, not universal thresholds.

A chat-template contract probe also found that the pinned LLM-jp template does **not** render the supplied `system` role. Existing training and inference used the same contract, so the measured scores remain internally consistent; however this means the learned LoRA projection carries more of the semantic-class boundary than the nominal system prompt. The rendered contract is now frozen as evidence.


## Reinstall-loop v1 — converged at loop 24 / max 50

A bounded reinstall-loop experiment was continued with a hard ceiling of **50 loops** and stopped early at the first measured convergence point. The optimization target is explicitly multi-dimensional: install-delta unique bytes, new filesystem objects, primitive installer capability, correctness, repair atomicity, cross-filesystem portability, update inheritance, canonical runtime bytes, and launcher bytes.

The measurement boundary matters: **0 B install delta is not a 0 B LLM**. It means that a reinstall projection adds no new unique file-content bytes because it reuses a canonical substrate.

| milestone | result | observation |
|---:|---|---|
| 0 | FAIL | Vendored copy duplicated **21,227 B** and relocation broke the adapter path (`.work/.work/...`). |
| 1–4 | PASS | wrapper → symlink → hardlink → self-reinstall; same-filesystem projection reached **0 unique B** while capabilities rose from 6 to 14. |
| 5–9 | PASS | verify, idempotent ensure, planning, safe repair, safe uninstall, and SHA-256 attestation appeared; primitive capability count reached **20**. |
| 10–11 | PASS | dispatcher/common-path refactoring shrank the workcell and exposed/fixed a real symlink-observer bug. |
| 12 | PASS | `/dev/shm` cross-filesystem trial predicted and used a **39 B symlink**; install/verify/doctor/uninstall all passed. |
| 13 | PASS | Reinstalling the already-canonical command reached the lower bound: **0 new objects / 0 unique B**, metadata-only noop (~0.07 ms internal observation). |
| 14 | PASS | duplicate-copy repair became atomic (`temp projection -> os.replace`) with no temporary leak. |
| 15 | PASS | Old thin installs inherited new capabilities **without being reinstalled**; the vendored Loop-0 copy remained stale. |
| 16–18 | PASS | canonical launcher shrank **151 B -> 135 B -> 133 B -> 132 B**, with existing hardlinks inheriting the change through the same inode. |
| 19 | REJECT | A 128 B unquoted launcher was smaller but failed when `$HOME` contained a space; rejected as robustness-dominated. |
| 20–23 | PASS | semantic-preserving commonization shrank the workcell **14,011 B -> 13,881 -> 13,582 -> 13,349 -> 13,304 B**. |
| **24** | **CONVERGED** | Two pure canonical reinstalls were both noop; structural delta from Loop 23 was zero and dev-v2 routing remained **64/64**. |

The final observed frontier on GAYA-CENTRAL is:

- same-filesystem new projection: **0 unique content bytes** (hardlink);
- already-canonical reinstall: **0 new objects / 0 unique content bytes**;
- cross-filesystem projection: **39 B symlink**;
- canonical launcher: **132 B**;
- workcell source: **13,304 B**;
- canonical runtime code (`workcell + router + finite-RAM control`): **28,795 B**;
- primitive surfaced capabilities: **20**;
- canonical code bytes per primitive capability: **~1.44 KB**, down from the Loop-0 vendored baseline **~3.54 KB/capability**;
- LoRA weight: **399,384 B**; checkpoint directory **6,816,979 B**;
- shared base-model snapshot observed locally: **311,063,611 B**;
- dev-v2 routing after convergence: **64/64 = 100%**, wall **5.927 s**.

The surprising emergent property was **evolution inheritance**. Thin wrapper/symlink/hardlink projections created in earlier loops automatically exposed the newest 20-capability runtime because they project one canonical substrate. The copied Loop-0 install stayed frozen. In this experiment, making installation thinner improved not only storage efficiency but also update propagation.

This convergence is **search-policy-relative**, not a universal optimum. Different explorers may admit different installer mechanisms, failure models, portability requirements, or objective axes and therefore converge elsewhere. The loop stopped at 24 because the next pure reinstall produced no structural Pareto delta; the remaining smaller launcher candidate was already shown to sacrifice robustness. The 50-loop ceiling was therefore not consumed artificially.

Raw convergence evidence is preserved in `results/reinstall-loop-convergence-v1.json`; the original Loop-0 relocation failure remains preserved separately rather than being rewritten away.

## Next physical experiments

1. Seal holdout-v4 **before** any repair of the v3 boundary misses; keep finite-RAM control changes orthogonal to semantic-boundary tuning.
2. Replace the blunt confidence threshold with a learned/structured handoff boundary and measure whether boundary-policy errors fall without increasing unsafe acceptance.
3. Expand the workcell only through typed specialists: read-only filesystem/git inspection, deterministic transforms, retrieval handoff, then Jev/CUA observation/action lanes. Never add arbitrary NL-to-shell execution.
4. Add a persistent-but-idle-unload router service governed by the new byte/PSI hysteresis policy so repeated semantic requests avoid ~6 s cold load while 0B-only periods can still release the 150M model.
5. Quantize the 150M + adapter lane (int8/int4/GGUF or equivalent) and remeasure accuracy, latency, load time, and RSS on GAYA-CENTRAL.
6. Test whether a smaller-than-150M Japanese substrate can retain the learned projection. Stop descending only when semantic fidelity or calibration actually breaks.
7. Treat reinstall-loop v1 as converged/frozen unless the canonical substrate, filesystem assumptions, or installer objective axes change; a changed search space should start a new loop series rather than tuning this result post hoc.
