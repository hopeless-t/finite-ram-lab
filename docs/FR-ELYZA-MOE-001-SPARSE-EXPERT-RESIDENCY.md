# FR-ELYZA-MOE-001 — Sparse Expert Residency Challenger

Status: **ANALYTIC / SHADOW DESIGN**

Stacked after: **FR-BONSAI-001 (#66)**

## Why this experiment exists

FR-BONSAI-001 attacks finite RAM with a dense 27B model: a decode token still needs the full ordered dense computation path, so nonresident blocks create repeated backing-store traffic.

ELYZA-Thinking-1.0-llm-jp-4-32b-a3b provides the complementary adversary:

> a model whose total stored parameter set is large, but whose routed execution width is sparse.

The Finite RAM Lab question is not whether the model is called "A3B". It is:

> **Can sparse routing be converted into a genuinely bounded resident working set, or does expert-union growth turn a nominally sparse model back into a storage-sized residency / I/O problem over time?**

This PR freezes that question before any physical run.

## Grounded model geometry

Primary sources:

- ELYZA model card: https://huggingface.co/elyza/ELYZA-Thinking-1.0-llm-jp-4-32b-a3b
- LLM-jp base model card: https://huggingface.co/llm-jp/llm-jp-4-32b-a3b-base
- LLM-jp config: https://huggingface.co/llm-jp/llm-jp-4-32b-a3b-base/blob/main/config.json
- ELYZA release: https://elyza.ai/news/2026/10/02/rsiresearch

The upstream model/config currently documents:

| property | value |
|---|---:|
| architecture | Qwen3MoeForCausalLM |
| layers | 32 |
| hidden size | 2,560 |
| MoE intermediate size | 960 |
| routed experts / layer | 128 |
| activated experts / token | 8 |
| context length | 65,536 |
| total parameters | 32,139,028,992 |
| activated parameters | 3,827,476,992 |
| embedding parameters | 503,316,480 |
| model-card license | Apache-2.0 |

ELYZA states that its released reasoning model is mid-trained and post-trained on the LLM-jp-4 32B-A3B base and recommends vLLM for serving. Those are upstream statements, not Finite RAM Lab measurements.

## Exact parameter decomposition

The base config is useful because the expert MLP geometry re-derives the published activated-parameter count exactly.

For one expert:

```text
P_expert
  = gate_proj + up_proj + down_proj
  = 3 * hidden_size * moe_intermediate_size
  = 3 * 2560 * 960
  = 7,372,800 parameters
```

Across all experts:

```text
P_all_experts
  = 7,372,800 * 128 * 32
  = 30,198,988,800
```

Therefore the non-expert/shared parameter set implied by the published total is:

```text
P_shared
  = 32,139,028,992 - 30,198,988,800
  = 1,940,040,192
```

The routed expert width for one token is:

```text
P_active_experts
  = 7,372,800 * 8 * 32
  = 1,887,436,800
```

and:

```text
P_shared + P_active_experts
  = 1,940,040,192 + 1,887,436,800
  = 3,827,476,992
```

which exactly matches the published activated-parameter count.

That identity is CI-checked by this PR.

## Critical correction: active parameters are not resident parameters

A single token activates only 8 of 128 experts per layer.

That does **not** imply that an arbitrarily long token trajectory needs only 8 experts resident.

Under a deliberately simple uniform-routing null model, the probability that one specific expert is not selected by one token is:

```text
1 - k/E
```

with:

```text
E = 128 experts
k = 8 selected experts/token
```

After `T` independently routed tokens, the expected number of distinct experts touched in one layer is:

```text
U(T) = E * [1 - (1 - k/E)^T]
     = 128 * [1 - (15/16)^T]
```

Selected points:

| tokens | expected distinct experts / layer |
|---:|---:|
| 1 | 8.000 |
| 4 | 29.123 |
| 16 | 82.423 |
| 64 | 125.942 |
| 256 | ~128.000 |

So even though instantaneous execution is sparse, the **expert union can become nearly dense over a short trajectory** when routing locality is weak.

This is a null model, not a claim about the real router distribution.

## The finite-residency problem

Define:

```text
R(t)
  = S_shared
  + C_expert(t)
  + K_KV(t)
  + A_runtime(t)
  + Q_io(t)
```

where:

- `S_shared` = always-needed shared/non-expert weights;
- `C_expert(t)` = currently resident expert cache;
- `K_KV(t)` = KV state;
- `A_runtime(t)` = allocator/runtime workspace;
- `Q_io(t)` = in-flight load/staging state.

The research objective is not to minimize weight residency alone.

A physical treatment is useful only if it preserves model semantics and foreground survival while moving the pressure knee.

## Static hot-set shadow model

Stage 0 uses a deliberately conservative analytic cache abstraction.

For each layer, reserve `C` expert slots.

The first panel sweeps:

```text
C = 8, 16, 32, 64 experts/layer
```

and uses a Zipf popularity curve only as a **locality sensitivity parameter**:

```text
alpha = 0.0   uniform
alpha = 0.75  moderate skew
alpha = 1.25  stronger skew
```

This does not assert that the real router is Zipf-distributed.

It answers a narrower question:

> how much expert-popularity concentration would be required for a bounded hot set to materially reduce cold-expert traffic?

For static top-`C` mass `H(C, alpha)`, the shadow miss width is:

```text
expected misses / layer / token
  = k * [1 - H(C, alpha)]
```

and the BF16 cold-expert traffic lower-bound proxy is:

```text
stream_bytes/token
  = misses_per_layer
  * P_expert
  * layers
  * 2 bytes
```

The corresponding pure-I/O upper bound is:

```text
tokens/s <= backing_bandwidth / stream_bytes_per_token
```

This is intentionally optimistic. It omits compute, page faults, queueing, synchronization, transforms, allocator effects, and cache-management overhead.

## BF16 shadow residency

Using the exact parameter decomposition and a synthetic 768 MiB runtime/KV reserve:

| expert slots / layer | shadow resident GiB |
|---:|---:|
| 8 | 7.879 |
| 16 | 11.395 |
| 32 | 18.426 |
| 64 | 32.489 |
| 128 | 60.614 |

The full published parameter set alone is about 59.864 GiB at BF16.

The published activated parameter count alone is about 7.129 GiB at BF16.

These values are **parameter-geometry conversions**, not measured vLLM process RSS.

The interesting 16-GiB-host region is therefore visible immediately:

```text
8-slot cache  -> geometrically plausible before runtime overhead
16-slot cache -> geometrically plausible in the shadow model
32-slot cache -> already outside a 16-GiB envelope
```

Whether either 8 or 16 slots is operationally useful depends almost entirely on routing locality, KV growth, runtime behavior, and backing-store cost.

## Why this is the right opponent for FR-BONSAI-001

The dense and sparse adversaries fail differently.

### FR-BONSAI-001 — dense 27B

Dense decode has an unavoidable property:

```text
nonresident dense block
-> revisit every generated token
-> repeated I/O unless pinned
```

Its main question is whether compression + a bounded streaming window can survive the reread tax.

### FR-ELYZA-MOE-001 — sparse 32B-A3B

Sparse decode changes the geometry:

```text
only 8/128 experts selected per layer per token
```

but introduces a new adversary:

```text
routing locality weak
-> expert union expands
-> hot-set miss rate rises
-> SSD/NVMe traffic rises
-> resident cache expands or decode stalls
```

This creates a clean comparative question:

> **Does sparsity create a real finite-RAM advantage after trajectory-level expert reuse is accounted for?**

Raw throughput between Bonsai and ELYZA is not directly comparable because architecture, packing, runtime, and quantization differ.

The comparison is about **memory-traffic shape**, not a benchmark winner.

## Frozen hypotheses

### H1 — activation width is not a residency guarantee

```text
P_active << P_total
```

does not imply:

```text
resident_bytes(sequence) ~= bytes(P_active)
```

because the expert union can expand across tokens.

### H2 — routing locality is the sparse-model control variable

At fixed cache size, stronger stable expert reuse should reduce expert load traffic.

If real traces show almost no reuse, the hot-set mechanism is rejected for that workload.

### H3 — an expert-cache pressure knee exists

As expert cache slots increase:

```text
resident bytes ↑
cold-expert traffic ↓
```

A useful operating region, if any, lies before either:

- RAM pressure enters a stall/cliff regime, or
- backing-store traffic dominates decode.

### H4 — sparse MoE can beat dense reread shape without becoming free

Compared with a dense streamed model, MoE should have an opportunity to avoid reading every expert every token.

But if route entropy is high and cache capacity is low, it may still collapse into severe expert thrash.

### H5 — phase and trajectory matter

Prompt prefill, short decode, long decode, tool-use bursts, and Japanese reasoning workloads may have different expert locality.

A policy qualified on one trajectory is not automatically qualified on another.

## Planned stages

### Stage 0 — source + analytic contract — this PR

Freeze:

- upstream geometry;
- exact parameter decomposition;
- expert-union null model;
- locality sensitivity panel;
- resident/cache equations;
- failure taxonomy;
- claim ceiling.

No physical model run.

### Stage 1 — runtime capability audit

Before any memory intervention, establish:

- whether the runtime maps or eagerly materializes expert tensors;
- whether router choices can be observed per layer/token;
- whether expert tensor residency can be measured;
- whether expert loads can be controlled independently from shared weights;
- whether KV placement can be measured separately;
- whether a treatment can preserve identical model outputs/settings.

If the runtime cannot expose these controls, record that as a result.

### Stage 2 — route-trace observation only

Run bounded prompts with **no eviction policy** and collect:

- expert IDs selected by layer/token;
- per-expert frequency;
- reuse distance;
- expert-union growth;
- entropy / concentration;
- phase boundaries;
- KV growth;
- baseline RSS / memory.current.

The first goal is to falsify or support locality before building a cache controller.

### Stage 3 — offline cache replay

Replay Stage-2 routes through:

- static top-C cache;
- LRU;
- frequency-biased cache;
- phase-reset cache;
- oracle future-aware cache as a lower bound.

This is where Finite RAM Lab can use reference/treatment methodology without changing the live runtime.

### Stage 4 — bounded physical residency treatment

Only if Stage 1 proves the runtime surface and Stage 3 predicts a meaningful region:

- pin shared weights;
- hold a bounded expert cache;
- move cold reconstructible experts to backing storage;
- record every expert miss/load;
- sweep the resident budget downward;
- preserve foreground work.

Do not infer success from process start or one completed token.

## Physical metrics

At minimum:

- `memory.current`, `memory.peak`, `memory.events`;
- PSI memory some/full;
- major/minor faults;
- NVMe throughput and queue latency;
- expert cache hit/miss by layer;
- expert load bytes;
- router entropy / hot-set mass;
- KV resident bytes;
- TTFT;
- decode tokens/s;
- p95/p99 token latency;
- foreground latency and survival.

## Failure-state biopsy

Never collapse a failed specimen into "OOM".

Classify at least:

```text
EAGER_FULL_MATERIALIZATION
SHARED_SET_TOO_LARGE
EXPERT_ACTIVE_WINDOW_TOO_LARGE
EXPERT_UNION_THRASH
ROUTING_HOTSET_DRIFT
KV_PRESSURE_KNEE
IO_QUEUE_SATURATION
FAULT_STORM
ALLOCATOR_GROWTH
FOREGROUND_DEGRADED
FOREGROUND_LOST
SEMANTIC_MISMATCH
OBSERVER_INCOMPLETE
UNKNOWN_EVIDENCE_GAP
```

The Chapter-II rule remains:

> name the state transition before interpreting the outcome.

## Rare-event lane

Near any observed knee, freeze unusual specimens rather than averaging them away.

Interesting rare states include:

- low-frequency expert-burst phases;
- sudden hot-set collapse;
- long reuse-distance spikes;
- high I/O with unchanged average router entropy;
- token-latency outliers without OOM;
- route traces whose observer completeness is suspect.

The rare-event question is not only "did the model crash?"

It is:

> which routing/residency state existed immediately before the trajectory changed?

## Host-safety boundary

This PR does not launch the model on the user's machine.

No self-hosted GitHub runner is required or introduced.

Any later host experiment remains bounded and must use the project's authorized local execution path, preserve foreground survival, and stop on evidence gaps or uncontrolled pressure.

## Claim ceiling

**ANALYTIC_ROUTING_RESIDENCY_SHADOW_MODEL_ONLY**

This PR establishes:

- source-grounded geometry;
- an exact active-parameter decomposition;
- a trajectory-level expert-union null model;
- a cache/locality sensitivity model;
- falsifiable hypotheses;
- a staged physical plan.

It does **not** establish:

- measured RAM savings;
- measured vLLM behavior;
- real router Zipf parameters;
- a working expert-eviction runtime;
- usable interactive performance;
- a safe universal 16-GiB configuration;
- any physical benefit on the user's host.
