# FR-DLSSNR-001 — Bit-Exact Neural Rendering as a Finite-Residency Oracle

Status: **SOURCE-GROUNDED ANALYTIC / EXPERIMENT DESIGN**

Stacked after: **FR-BONSAI-001**

Upstream reference frozen at:

- repository: `maanHimself/OpenDLSS-NR`
- commit: `9d08f4184bbcb9d858e2fb7a7834ec0837a9d2f1`
- upstream README: https://github.com/maanHimself/OpenDLSS-NR
- network overview: https://github.com/maanHimself/OpenDLSS-NR/blob/main/docs/README.md
- execution notes: https://github.com/maanHimself/OpenDLSS-NR/blob/main/docs/execution.md
- numerics contract: https://github.com/maanHimself/OpenDLSS-NR/blob/main/docs/numerics.md

## Why this experiment exists

FR-BONSAI-001 asks how far a large dense model can move from "all weights resident" toward a bounded working window.

FR-DLSSNR-001 attacks the same finite-residency question from the opposite direction:

> use a comparatively small, real-time neural renderer with an unusually strong semantic oracle, then reduce or reshape residency while requiring byte-exact behavior.

OpenDLSS-NR is useful because the upstream project separates semantic requirements from implementation choices and exposes multiple execution routes that are intended to preserve exact results.

This makes it possible to ask a stronger question than "does the frame still look right?":

> **How much live memory can be removed, fused, streamed, or reconstructed before the first byte-level semantic divergence appears?**

That is a direct Finite RAM Lab question.

## Grounded upstream geometry

At the frozen upstream reference, OpenDLSS-NR documents:

- DLSS-NR build 310.8.0 network shape;
- a U-net of shifted-window transformer blocks with a global ViT at the bottom;
- 71 Swin / ViT blocks over six pooling levels;
- FP8 E4M3 activations with FP16 accumulation;
- approximately 141 MiB of weights;
- 75 published comparable internal boundaries reported byte-for-byte exact against reference captures;
- a second WebGPU implementation reported to produce the same bytes from the same captures without tensor cores, hardware FP8, cross-block fusion, or counter chaining;
- 241 dispatches per frame in the default Vulkan route at every published resolution.

Published RTX 4070 SUPER minimum whole-network times:

| resolution | minimum time |
|---|---:|
| 512x512 | 2.72 ms |
| 768x768 | 2.83 ms |
| 1920x1080 | 7.77 ms |
| 2560x1440 | 12.6 ms |
| 3840x2160 | 29.3 ms |

These are upstream measurements, not Finite RAM Lab measurements.

Important scope correction:

- this is **DLSS Neural Rendering**, not DLSS-SR;
- input and output are the same resolution;
- the repository does not ship NVIDIA model weights;
- reference fixtures are not shipped;
- a physical parity run therefore requires separately supplied compatible weights and fixture captures.

## Why bit-exactness changes the research design

Many memory optimizations have a weak semantic gate:

`program completed`

or:

`output metric remained acceptable`.

FR-DLSSNR-001 instead treats exactness as a hard invariant.

For policy `pi` and dispatch step `t`, define the live memory state:

```text
M_pi(t) =
    W_pi(t)   resident weights
  + A_pi(t)   live activations
  + S_pi(t)   scratch / attention workspace
  + H_pi(t)   history / temporal state
  + G_pi(t)   staging / transfer state
```

and:

```text
M_peak(pi) = max_t M_pi(t)
```

For an imposed memory budget `B`:

```text
budget_ok(pi, B) := M_peak(pi) <= B
```

The semantic constraint is:

```text
parity_ok(pi) :=
    every declared comparable boundary is byte-exact
    AND head parity is exact when declared
    AND final output parity is exact when declared
    AND production repeats agree
```

A policy is scientifically feasible only when:

```text
qualified(pi, B) :=
    budget_ok(pi, B)
    AND parity_ok(pi)
    AND evidence_complete(pi)
    AND validation_clean(pi)
```

This makes semantic survival a constraint, not a soft score.

## Ozaki-style finite-residency optimization

The first optimization is deliberately lexicographic.

Do not trade correctness for memory.

Order objectives as:

1. preserve complete bit-exact parity;
2. minimize peak live residency;
3. minimize frame latency / tail latency;
4. minimize transfer, rematerialization, and synchronization cost.

Only after exactness is satisfied may a scalar performance cost be considered.

A later measured policy objective may use:

```text
J(pi | parity_ok = 1) =
    alpha * M_peak(pi) / M_peak(reference)
  + beta  * T_frame(pi) / T_frame(reference)
  + gamma * XferBytes(pi) / XferBytes(reference)
  + delta * SyncCost(pi) / SyncCost(reference)
```

No `alpha/beta/gamma/delta` values are frozen here.

## Natural reference/treatment arms already exposed upstream

The upstream tuning surface is unusually useful because several treatments are already designed to preserve exact bytes.

### REF_UNFUSED

`DLSS5VK_UNFUSED=1`

The upstream README states that this reference route materializes every intermediate.

Finite RAM interpretation:

> high materialization / high observability reference arm.

### FAST_EXACT

Default route.

Uses fused kernels, PTX fast paths, streamed global attention where selected, and barrier-free chaining.

Finite RAM interpretation:

> optimized live-set / synchronization treatment arm.

### CHAIN_OFF

`DLSS5VK_CHAIN=0`

Places barriers between launches instead of counter chaining.

Finite RAM interpretation:

> separate synchronization savings from representation-residency savings.

### ATTN_STREAM_OFF / ON

`DLSS5VK_ATTN_STREAM=0|1`

Finite RAM interpretation:

> isolate the residency / scratch / traffic effect of streamed global attention.

### SINGLE_FUSION_ABLATIONS

Examples documented upstream:

- `DLSS5VK_NO_FUSE_PRE=1`
- `DLSS5VK_NO_FUSE_POOL=1`
- `DLSS5VK_NO_FUSE_UPRES=1`
- `DLSS5VK_NO_FUSE_POST=1`

Finite RAM interpretation:

> estimate the marginal live-set and latency contribution of individual fusion boundaries without changing intended semantics.

## Core falsifiable hypotheses

### H1 — exact semantics do not require maximal materialization

If the upstream exactness claims hold under instrumentation, then:

```text
M_peak(FAST_EXACT) < M_peak(REF_UNFUSED)
```

should be observable for at least one resolution while parity remains exact.

If not, the "fusion reduces live residency" hypothesis is rejected for the measured memory domain.

### H2 — synchronization and residency are separable costs

If `CHAIN_OFF` materially changes latency without materially changing measured live bytes, then chaining is primarily a scheduling/synchronization optimization rather than a residency optimization.

### H3 — streamed attention has a measurable residency/traffic frontier

For global attention:

```text
streaming benefit = lower peak workspace/residency
streaming cost    = extra movement / scheduling / compute overhead
```

The sign and magnitude must be measured; they are not assumed.

### H4 — bit-exact failure localizes the pressure boundary

Because comparable boundaries are published, the first divergence can be localized to a specific boundary rather than reported only as a bad final frame.

A pressure-induced semantic failure should therefore be classified as:

```text
first_bad_boundary
+ memory state immediately before divergence
+ active execution policy
```

rather than "render failed."

### H5 — implementation independence can test semantic vs hardware necessity

The WebGPU port is reported upstream as byte-exact despite lacking tensor cores, hardware FP8, block fusion, and chaining.

This supports a testable distinction:

```text
semantic requirement != accelerator-specific implementation choice
```

Finite RAM Lab must verify this only from supplied fixtures; the upstream statement is not treated as our own reproduced result.

## Stage 0 — source contract

This PR performs Stage 0 only.

Freeze:

- upstream commit;
- known network geometry;
- parity contract;
- execution toggles;
- experiment equations;
- failure taxonomy;
- claim ceiling.

No GPU run is performed.

## Stage 1 — allocation and liveness observation

On a compatible machine with legal weights and fixtures:

1. run `REF_UNFUSED` and `FAST_EXACT` with identical fixture/resolution;
2. record exactness first;
3. record device-local allocation high-water mark;
4. record host-visible staging high-water mark;
5. instrument activation/scratch allocation lifetime where possible;
6. record dispatch, barrier, and transfer counts;
7. record frame time distribution.

Suggested initial resolutions:

```text
512x512
768x768
1920x1080
```

Do not begin at 4K merely to manufacture pressure.

## Stage 2 — deterministic budget sweep

After measurement instrumentation is qualified, introduce an explicit allocator budget or equivalent deterministic allocation cap.

Do not rely on accidental system OOM as the experiment mechanism.

For each policy:

```text
B0 -> B1 -> B2 -> ... downward
```

until one of these occurs:

- allocation cannot be satisfied;
- parity becomes incomplete;
- first boundary mismatch occurs;
- latency crosses the predeclared ceiling;
- evidence becomes incomplete.

Define the candidate exact-residency knee:

```text
B* = minimum tested budget
     for which all exactness and evidence gates still pass
```

This is an empirical knee for the measured hardware, fixture, resolution, and implementation.

It is not a universal DLSS memory requirement.

## Stage 3 — knee biopsy and rare-event lane

Near `B*`, repeat identical fixtures and freeze every noncanonical specimen.

Classify at least:

- `EXACT_PASS`
- `ALLOC_BUDGET_REJECT`
- `DEVICE_OOM`
- `FIRST_BOUNDARY_MISMATCH`
- `HEAD_MISMATCH`
- `OUTPUT_MISMATCH`
- `TEMPORAL_STATE_INVALID`
- `TRANSFER_THRASH`
- `SYNC_STALL`
- `VALIDATION_ERROR`
- `FIXTURE_INCOMPLETE`
- `UNSUPPORTED_HARDWARE`
- `UNKNOWN_EVIDENCE_GAP`

A rare mismatch is a specimen, not noise to average away.

## Stage 4 — temporal extension

Only after single-frame parity remains stable near the residency knee should the temporal path be studied.

The temporal experiment must separate:

```text
single-frame exactness
!= temporal-state survival
!= long-trajectory exactness
```

This directly mirrors the existing Finite RAM Lab distinction between one-step success, endpoint success, and trajectory survival.

## Measurements

Primary semantic measurements:

- boundary exactness count;
- first mismatching boundary;
- head exactness;
- final output exactness;
- repeated-production agreement.

Primary residency measurements:

- device-local allocated bytes;
- device-local peak bytes;
- host-visible staging bytes;
- activation live bytes;
- scratch live bytes;
- history / temporal live bytes;
- transfer bytes per frame.

Performance measurements:

- dispatch count;
- barrier count;
- frame time min / median / p95 / p99;
- GPU utilization where available;
- host CPU time;
- transfer / queue time.

Environment receipt:

- GPU model;
- driver;
- Vulkan extensions;
- OpenDLSS-NR commit;
- model manifest hashes;
- fixture manifest hashes;
- resolution;
- execution toggles.

## Separation from the Linux memcg lane

This track is **not** evidence about Linux memcg Chapter-II mechanisms.

The primary constrained resource may be VRAM/device-local memory, with host-visible staging as a secondary resource.

Transferable methodology:

- finite residency;
- pressure knee;
- exact reference/treatment pairing;
- failure-state biopsy;
- rare-event preservation;
- trajectory survival;
- observation before intervention.

Non-transferable without re-proof:

- memcg thresholds;
- page-charge batching;
- local Governor policy thresholds;
- OOM victim semantics.

## Why this complements FR-BONSAI-001

FR-BONSAI-001 is large-model, SSD-backed, throughput-hostile, and primarily host-RAM oriented.

FR-DLSSNR-001 is smaller, real-time, GPU-residency oriented, and has a much stronger semantic oracle.

Together they probe two different failure regimes:

```text
large state + weak exact oracle
versus
smaller state + extremely strong exact oracle
```

If the same finite-working-set principles survive both, that is stronger evidence for the abstraction than either workload alone.

## Claim ceiling

**SOURCE_GROUNDED_BITEXACT_RESIDENCY_DESIGN_ONLY**

This document establishes:

- a source-grounded experiment target;
- exactness constraints;
- mathematical variables;
- falsifiable hypotheses;
- measurement and failure contracts.

It does **not** establish:

- any Finite RAM Lab OpenDLSS-NR physical result;
- any measured memory reduction;
- any universal VRAM requirement;
- any Linux memcg conclusion;
- possession or redistribution rights for NVIDIA weights or fixture captures;
- that the user's current machine satisfies the upstream Vulkan/NVIDIA requirements.
