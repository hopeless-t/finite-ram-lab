# FR-REP-001 — Representation × Placement Graph

Status: **SYNTHETIC REPRESENTATION / PLACEMENT QUALIFICATION**

Parent: **FR-SOOM-002L**

## Goal

Finite RAM Lab already treats RAM, compressed RAM, SSD, VRAM/GTT and other
memory surfaces as coupled resources.

This lane adds another dimension:

**the same semantic state may have multiple physical representations.**

Candidate representation technologies include AWQ, GPTQ, NF4 and native BitNet
models.

GGUF is deliberately placed on a different axis because it is a container /
metadata format, not a quantization algorithm.

Cloud object storage is also placed on a different axis because it is a
placement tier, not a representation.

The resulting planner state is:

```text
semantic state
   × model compatibility
   × numeric / weight representation
   × container
   × placement
   × deadline
   × quality floor
```

## Source taxonomy

### AWQ

AWQ is treated as a low-bit weight quantization method.

The source method uses activation statistics to identify salient channels and
protect quantization quality without modeling AWQ itself as a storage tier.

### GPTQ

GPTQ is treated as a one-shot post-training weight quantization method using
approximate second-order information.

It is another representation-generation method, not a placement.

### NF4

NF4 is treated as a numeric representation.

It is not synonymous with AWQ or GPTQ.

Its QLoRA origin also demonstrates that reducing weight representation can move
pressure elsewhere, such as optimizer and dequantization behavior.

### GGUF

GGUF is modeled as a container.

It has tensor metadata, tensor types, offsets and alignment.

The synthetic planner gives GGUF **no compression credit** by itself.

A future remote-range loader could use tensor offsets to request selected object
ranges, but that would be a loader feature built on top of GGUF and object
storage; it is not claimed as stock llama.cpp behavior.

### BitNet b1.58

BitNet is modeled as a native model-encoding / architecture class.

The planner explicitly rejects this invalid operation:

`arbitrary conventional model -> runtime BitNet demotion`.

A BitNet-native checkpoint can be a very compact candidate.

An unrelated FP16/AWQ/GPTQ model cannot simply be treated as BitNet because a
memory controller wants fewer bytes.

## Cloud tier

Cloud object storage is permitted as a cold placement class.

The synthetic model assigns it:

- very large capacity;
- zero local storage residency;
- network dependency;
- higher base latency;
- limited bandwidth;
- deadline eligibility rules.

The current lane is intentionally conservative:

- HOT state: cloud-ineligible;
- WARM state: cloud-ineligible;
- COLD model shard: cloud-eligible.

This does **not** mean cloud can never serve warm state.

It means that promotion requires measured network evidence rather than assuming
the internet is a second SSD.

Object stores that support byte-range retrieval make a future chunked remote
backing experiment possible.

## Frozen synthetic candidates

Representations:

| representation | relative bytes | quality proxy | role |
|---|---:|---:|---|
| FP16 | 1.0 | 1.000 | conventional baseline |
| AWQ4 | 0.25 | 0.985 | synthetic 4-bit candidate |
| GPTQ4 | 0.25 | 0.982 | synthetic 4-bit candidate |
| NF4 | 0.25 | 0.980 | synthetic 4-bit candidate |
| BitNet b1.58 | 0.09875 | 0.995 | native-only candidate |

These quality values are **synthetic controls**, not benchmark claims about the
real technologies.

Placements:

| placement | base latency | bandwidth |
|---|---:|---:|
| VRAM | 0.05 ms | 100000 MiB/s |
| RAM | 0.10 ms | 20000 MiB/s |
| SSD | 0.30 ms | 3000 MiB/s |
| CLOUD_OBJECT | 35 ms | 250 MiB/s |

Again: these are synthetic controls, not measurements.

## Frozen state classes

### HOT_WEIGHT_SHARD

- FP16-equivalent size: 512 MiB
- deadline: 20 ms
- quality floor: 0.980
- cloud: prohibited

Selected:

`AWQ4 -> RAM`

Synthetic fetch/decode latency:

`8.0 ms`

### WARM_EXPERT_SHARD

- FP16-equivalent size: 512 MiB
- deadline: 300 ms
- quality floor: 0.980
- cloud: prohibited

Selected:

`AWQ4 -> SSD`

Synthetic latency:

`44.47 ms`

### COLD_MODEL_SHARD

- FP16-equivalent size: 2048 MiB
- deadline: 10 s
- quality floor: 0.980
- cloud: permitted

Selected:

`AWQ4 -> CLOUD_OBJECT`

Synthetic latency:

`2084.5 ms`

This demonstrates the intended role of cloud:

`cold capacity extension with promotion before use`.

### BITNET_NATIVE_SHARD

- native BitNet model class
- FP16-equivalent reference size: 2048 MiB
- deadline: 1 s

Selected:

`BITNET_B1_58 -> SSD`

The conventional-model compatibility probe correctly rejects the same
representation for HOT_WEIGHT_SHARD.

## Force-cloud counterfactual

The experiment also forces AWQ4 + CLOUD_OBJECT regardless of cloud policy.

Synthetic results:

- HOT 512-MiB-equivalent shard: ~548.5 ms > 20-ms deadline -> FAIL
- WARM 512-MiB-equivalent shard: ~548.5 ms > 300-ms deadline -> FAIL
- COLD 2048-MiB-equivalent shard: 2084.5 ms < 10-s deadline -> PASS

Therefore:

`cloud capacity != deadline-safe residency`.

Cloud is a **deadline class**, not a universal escape hatch.

## Resource objective

Residency bytes are tier-typed.

The planner does **not** collapse VRAM and host RAM into one generic volatile
byte count.

Frozen lexicographic objective:

```text
min accelerator-resident bytes
min host-RAM-resident bytes
min local-storage bytes
min network-fetch bytes
max quality proxy
min latency
```

The first qualification attempt exposed why this matters: AWQ4/RAM and
AWQ4/VRAM both occupied 128 MiB, and a fungible-byte objective chose VRAM only
because it was faster.

That is rejected by this lane.

`128 MiB VRAM != 128 MiB host RAM`.

This is a direct representation-level instance of the earlier
`capacity is topology weighted` invariant.

## Primary findings

### 1. Representation choice is not placement choice

AWQ/GPTQ/NF4 answer:

`how is the state encoded?`

RAM/SSD/Cloud answer:

`where is the state backed right now?`

The controller must optimize both.

### 2. Container is not quantizer

GGUF carries tensors and metadata.

It does not receive a 4-bit compression ratio merely by being GGUF.

### 3. Architecture is not runtime demotion

BitNet-native models are valuable candidates.

BitNet is not a magic emergency action that turns any current model into a
1.58-bit model without semantic/model changes.

### 4. Residency bytes are tier-typed, not fungible

A byte of accelerator residency, host RAM, local SSD, or remote object storage is not interchangeable.

### 5. Cold cloud is feasible before hot cloud

A large network-backed tier can reduce local storage pressure strongly.

But promotion latency and network tails must be priced against the state
deadline.

## New governor architecture

```text
semantic object
      |
      v
compatibility filter
      |
      +-- conventional -> FP16 / AWQ / GPTQ / NF4 / ...
      |
      +-- BitNet native -> BitNet representation
      |
      v
quality floor
      |
      v
container choice
      |
      v
placement graph
 VRAM <-> RAM <-> compressed RAM <-> SSD <-> cloud
      |
      v
deadline / tail-risk qualification
      |
      v
promotion, demotion, drop, or regenerate
```

## Security and privacy boundary

A future cloud tier must include an eligibility field.

At minimum, distinguish:

- public/re-downloadable model weights;
- licensed but remotely storable weights;
- encrypted private artifacts;
- user conversation/KV state;
- secrets / credentials.

Cloud placement should fail closed when the object is not eligible.

This lane does not upload anything.

## Next: FR-REP-002

The next experiment should add stochastic network tails and an explicit local
cache.

Compare:

1. SSD_ONLY
2. CLOUD_ON_DEMAND
3. CLOUD_PREFETCH
4. CLOUD_PLUS_LOCAL_RANGE_CACHE
5. MULTI_REPRESENTATION_CACHE

The key question:

> How much local SSD/RAM cache is needed before cloud-backed model shards stop
> causing semantic deadline failures?

Then combine this with STRATA-FAMILY-001 and FR-SOOM-002K demand folding.

## Claim ceiling

**SYNTHETIC_REPRESENTATION_PLACEMENT_GRAPH_ONLY**

No real quantization is performed.

No model is converted.

No cloud object is uploaded or downloaded.

No live memory policy is changed.
