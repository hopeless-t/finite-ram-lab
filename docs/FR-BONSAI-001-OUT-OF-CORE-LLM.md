# FR-BONSAI-001 — Out-of-Core 27B as a Finite-RAM Adversarial Workload

Status: **ANALYTIC / SHADOW DESIGN**

Parent: **FR-SOOM-002J**

Upstream source frozen for Stage 0 geometry:

- repository: `PrismML-Eng/Bonsai-demo`
- commit: `bfaea577522626b883f755236878e4583f3d6e68`
- observed: 2026-10-03 source refresh


## Why this experiment exists

FR-SOOM-002J established a synthetic controller that chooses among RAM, compressed RAM, SSD, drop/rebuild, and process sacrifice under a pressure deadline.

FR-BONSAI-001 turns that abstract tiering problem into a deliberately hostile workload:

> Can a dense 27B ternary model complete inference while its resident weight set is held far below the packed model size, without sacrificing foreground work?

Bonsai 2 27B is useful because the model vendor has already compressed the weights aggressively. The remaining question is therefore not merely "can weights be quantized?" but whether the operating/runtime system can exploit **time, re-fetchability, phase, and semantic value** as memory resources.

## Grounded model geometry

Upstream Bonsai 2 documentation currently describes:

- Qwen3.8-27B-derived hybrid attention;
- 64 language backbone blocks;
- 24.35B language-backbone parameters;
- 2.54B embedding / LM-head parameters;
- PTQ1_0 at about 5.95 GB;
- PQ2_0 at about 7.21 GB;
- optional 4-bit KV support in the demo runtime.

Sources:

- https://github.com/PrismML-Eng/Bonsai-demo
- https://github.com/PrismML-Eng/Bonsai-demo/blob/main/MODEL-FORMATS.md
- https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf

These values define experiment geometry only. They are not host measurements.

## Core distinction: partial loading is not partial execution

The proposed mechanism may keep only a subset of weight blocks resident, but a dense decode token still requires the model's full ordered computation path.

This yields two very different phases.

### Decode

For each generated token, every nonresident block must eventually be made available again.

If:

- N = total transformer blocks;
- P = blocks permanently pinned in RAM;
- S_block = average packed block bytes;
- B_io = sustained backing-store bandwidth;

then the optimistic I/O lower bound is:

```text
bytes_read_per_decode_token = (N - P) * S_block

decode_tps_io_bound =
    B_io / bytes_read_per_decode_token
```

This is a lower bound. It omits page-fault overhead, queueing, transform cost, runtime synchronization, compute time, and cache interference.

### Prefill

For a prompt of L tokens, a streamed block can be loaded once and applied across many input tokens before eviction.

The same weight movement is approximately amortized as:

```text
prefill_weight_io_per_input_token =
    streamed_weight_bytes / L
```

Therefore FR-BONSAI-001 predicts a large asymmetry:

> **out-of-core prefill should be much easier than out-of-core autoregressive decode.**

That prediction is falsifiable.

## Resident working-window model

The first analytic model separates RAM into:

```text
resident budget
  = pinned non-block weights
  + runtime / KV reserve
  + double-buffered streaming window
  + permanently pinned transformer blocks
```

The streaming window is not treated as free cache. Its purpose is to overlap:

```text
execute window A
        ||
prefetch window B
```

Permanent block pinning is accounted separately because only permanently retained blocks reduce repeated decode traffic.

## Initial factorial panel

Frozen shadow factors:

| factor | values |
|---|---|
| pack | PTQ1_0, PQ2_0 |
| resident budget | 1, 2, 4, 6 GiB |
| backing bandwidth | 1000, 2500, 5000 MiB/s |
| streaming window | 2 blocks |
| buffering | double |
| synthetic runtime + KV reserve | 768 MiB |
| prefill length | 4096 tokens |

The 768-MiB reserve is deliberately synthetic. It exists to prevent the analytic model from pretending all RAM is weight RAM.

## Finite RAM Lab interpretation

The important control surface is not merely "swap or do not swap."

Candidate controller actions are:

```text
KEEP
  -> PIN hot blocks
  -> SHRINK streaming window
  -> QUANTIZE / SHRINK KV
  -> DONTNEED cold pages
  -> SPILL reconstructible state
  -> THROTTLE inference
  -> preserve foreground task
  -> process sacrifice only as a terminal action
```

This turns memory management into a survival-control problem.

A future physical controller should minimize a multi-objective cost such as:

```text
J =
    alpha * resident_bytes
  + beta  * inference_latency
  + gamma * backing_store_traffic
  + delta * foreground_latency
  + epsilon * P(foreground_loss)
```

subject to a pressure-knee constraint:

```text
memory.current < qualified pressure frontier
```

No scalar weights are frozen in this PR.

## What would count as a meaningful win?

Not merely:

> "the 27B process started."

A useful result must preserve task completion under a bounded resident set while recording the cost paid elsewhere.

Primary physical success dimensions:

1. model inference completes;
2. resident memory stays inside the declared budget or qualified knee;
3. foreground workload survives;
4. pressure does not enter uncontrolled full-stall;
5. evidence is complete;
6. latency and I/O cost are reported rather than hidden.

The physical study should report at minimum:

- memory.current / memory.peak;
- memory.events;
- PSI memory some/full;
- minor and major faults;
- NVMe throughput and queue latency;
- time-to-first-token and decode tokens/s;
- foreground latency and survival;
- refault/reload bytes;
- KV resident bytes.

## Pressure-knee experiment

A future host run should sweep resident budgets downward rather than selecting one heroic low number.

Suggested sequence:

```text
6 GiB
 -> 4 GiB
 -> 2 GiB
 -> 1 GiB
```

At every point classify:

```text
COMPLETES_CLEANLY
COMPLETES_WITH_LATENCY_CLIFF
IO_BOUND
FAULT_STORM
PRESSURE_STALL
FOREGROUND_DEGRADED
FOREGROUND_LOST
UNKNOWN_EVIDENCE_GAP
```

The first sharp transition is the candidate pressure knee.

## Failure-state biopsy

A failed run must not collapse into "OOM."

Capture whether the terminal mechanism was:

- insufficient fixed working window;
- repeated model-weight reread;
- page-fault amplification;
- NVMe queue saturation;
- KV growth;
- runtime allocator growth;
- compute stall;
- foreground contention;
- kernel reclaim behavior;
- evidence loss.

This preserves the Chapter-II rule:

> Name the state transition before interpreting the outcome.

## Rare-event lane

Once a stable boundary is found, repeated trials should search for low-frequency states near that knee.

Examples:

- unusually low reread traffic;
- unusually high refault amplification;
- scheduler-induced long-tail stalls;
- foreground latency spikes without OOM;
- apparent completion with incomplete telemetry.

Rare specimens should be frozen, not averaged away.

## What this PR does now

This PR adds only an analytic shadow model and CI-checked experiment contract.

It does **not**:

- patch llama.cpp;
- claim per-block eviction is currently exposed by the runtime;
- execute the user's host;
- enable a memory governor;
- kill or signal processes;
- claim a usable interactive decode rate.

The physical implementation is a later qualification step.

## Physical implementation questions

Before launch, inspect the PrismML llama.cpp fork and determine whether the required controls are available or need instrumentation:

1. Can model tensors be mapped without eagerly faulting the full file?
2. Can selected block tensors be explicitly prefetched?
3. Can cold mapped ranges be advised DONTNEED safely between phases?
4. Can block/tensor residency be observed without perturbing the run excessively?
5. Can KV placement and weight placement be controlled independently?
6. Can prefill and decode use different residency policies?
7. Does GPU offload make the host-RAM experiment semantically invalid for a given arm?

If the runtime cannot express the intended intervention, record that as a result rather than silently changing the experiment.

## Claim ceiling

**ANALYTIC_OUT_OF_CORE_LLM_SHADOW_MODEL_ONLY**

The current PR establishes equations, experiment geometry, falsifiable predictions, and CI invariants. It does not establish physical benefit.
