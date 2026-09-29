# STRATA-001 — Source-grounded intake for finite-ram-lab

> **Source repo:** Niko1221/Strata
> **Observed head:** 3ce2523c2823687de5372be3af58534f56cbf286
> **Observed date:** 2026-09-30 JST
> **Status:** EXTERNAL INTAKE / NO ABSORB DECISION YET

## Why Strata matters here

Strata is a live implementation of a finite-memory placement problem:

- a very large sparse MoE model;
- limited VRAM;
- larger but finite host RAM;
- SSD-backed lookup data;
- per-request working sets whose hotness changes over time.

The relevant lesson is not merely that a large model runs on a gaming PC.

The relevant lesson is that Strata repeatedly converts **memory placement into an explicit control problem**.

## 1. Three-tier residency is explicit

Current documented architecture:

- VRAM: hot routed experts and active compute state;
- RAM: full expert population and streamed KV / staging;
- SSD: the large PLE lookup table.

This is directly analogous to finite-ram-lab's HOT/WARM/COLD framing.

Important distinction:

Strata does not treat tiers as static capacity buckets.

It moves work and residency policy according to observed bottlenecks.

## 2. Expert cache is a working-set controller

Source:
`include/strata/core/expert_cache.hpp`

The cache maps:

`(layer, expert) -> resident slot | not resident`

The code explicitly rejects several unsafe simplifications:

- planner estimates are checked against live free VRAM;
- cache bytes are verified against host source bytes;
- profile ranking is measured on held-out routing traces;
- eviction is not silently invented before it is measured.

A particularly relevant historical failure is documented in the source:

global arrival-order admission let early layers consume the entire cache.

Measured example:

- 256 slots globally;
- only about 2.97% cache hits;
- a per-layer allocation model predicted much larger useful hit rates.

Lesson for finite-ram-lab:

**capacity alone is not the state variable. Allocation topology can dominate capacity.**

This is strongly resonant with the current H10/H32/PTE result.

## 3. Static profile + adaptive hotness

Source:
`tools/make_profile.py`

Strata builds a complete ranking over all (layer, expert) pairs.

Order:

1. base profile;
2. pairs seen in routing traces, frequency-ranked;
3. every remaining pair, interleaved across layers.

The runtime then has an adaptive tier that swaps in experts used by the current conversation.

This is a concrete hybrid:

`prior hotness + online working-set adaptation`

finite-ram-lab analogue:

a memory controller should not rely only on:
- global historical frequency;
- or only on immediate recency.

A hybrid prior + online correction is worth testing.

## 4. Borrowable residency is more valuable than fixed reservation

Source:
`src/program/generate.cpp`
`src/prefill/prefill.cpp`
`bench/results/2026-09-28-prefill-speed/README.md`

Prompt processing can borrow VRAM slots normally used by the expert cache.

`--prefill auto` chooses the largest chunk whose scratch buffers fit in the slots that can be borrowed.

Measured example from Strata:

- attention/MoE scratch sharing reduced a 4096-token chunk from about 2.84 GiB borrowed to 1.78 GiB;
- larger chunks reduce streamed expert bytes per token;
- after prompt processing, the borrowed region is returned/refilled as expert cache.

This is not ordinary caching.

It is **time-multiplexed ownership of the same physical capacity**.

finite-ram-lab should treat this as a first-class pattern:

`resident owner A -> bounded lease to phase B -> deterministic return/rebuild`

This is potentially more important than a static HOT/WARM policy.

## 5. Pinned-memory scarcity is handled as a pipeline problem

Source:
`src/prefill/prefill.cpp`

Some expert data cannot remain pinned.

Rather than synchronously copying pageable data on the launch thread, helper threads stage it into a bounded pinned ring ahead of DMA.

The ring depth itself is tuned because too much buffering consumes cache capacity and can make the system slower.

Lesson:

**when a fast tier is scarce, staging depth is an optimization variable, not “as much as possible”.**

This matches finite-ram-lab's broader pressure-knee theme.

## 6. SSD traffic is reordered rather than merely cached

Source:
`src/ngram/ple_reader.cpp`

PLE row requests:

- deduplicate reads that share an aligned page;
- sort pending jobs by file offset;
- submit near-sequential reads;
- use bounded in-flight buffers and a row cache.

This turns sparse logical access into friendlier physical I/O.

The finite-ram-lab abstraction is:

`logical working set != physical transfer schedule`

A reducer/reorderer can lower transport cost without changing the requested data set.

## 7. KV streaming explicitly trades VRAM for RAM to free expert residency

Source:
`include/strata/core/layer.hpp`
and project documentation.

At long context, Strata can keep only a resident window of KV in VRAM and store the rest in pinned host memory.

The freed VRAM is then available for more experts.

The important pattern is:

`move a high-volume but streamable state down one tier to keep latency-sensitive sparse state up one tier`

This is a stronger formulation than “spill when full.”

It is **cross-class memory substitution**.

## 8. Multi-GPU results show residency saturation and a new bottleneck

Source:
`bench/results/2026-09-29-layer-split/README.md`

In the tested two-GPU Coder configuration:

- routed-expert hit rate reached roughly 98-100%;
- beyond that point, adding residency no longer dominated;
- per-layer GPU stage latency became the limiter;
- adding a slower third GPU made the overall system worse.

Lesson:

**once one bottleneck is saturated, additional capacity can reduce performance by exposing transport/stage overhead.**

This is directly relevant to finite-ram-lab's search for knees rather than maxima.

## 9. Current rapid-development signal

Recent observed changes include:

- engine 0.1.23 and 0.1.24;
- QSA prompt selection moved onto tensor cores;
- long-context selection cost reduced substantially;
- 8 GB-card prompt-buffer fallback;
- multi-GPU per-device shared-memory fix;
- batching of speculative verify-window kernels;
- new speed measurements and calibration paths.

The repository is currently changing fast enough that any borrowed mechanism should be pinned to an exact commit before reproduction.

## 10. Immediate finite-ram-lab hypotheses derived from Strata

### STRATA-H1 — Leaseable residency

A fixed memory region that alternates ownership by execution phase can outperform static partitioning even when total peak demand is unchanged.

### STRATA-H2 — Topology before size

When resident slots are allocated across independent demand groups, per-group allocation topology can dominate total slot count.

### STRATA-H3 — Cross-class substitution

Moving large sequential/streamable state to a slower tier can improve the whole system if it frees fast-tier capacity for sparse latency-sensitive state.

### STRATA-H4 — Staging knee

Pinned/staging buffer depth has an interior optimum because deeper rings improve overlap but consume the same scarce capacity needed by the working set.

### STRATA-H5 — Saturation transition

Once cache hit rate approaches saturation, the system's dominant bottleneck shifts to per-stage compute/transport, so more cache or more devices can stop helping or become harmful.

## Council pre-classification

**ABSORB as research patterns:**
- explicit residency receipts;
- leaseable phase ownership;
- prior + online hotness;
- bounded staging rings;
- physical I/O reorder/dedup;
- bottleneck-shift detection after cache saturation.

**BORROW source ideas, not code yet:**
- expert-profile ranking;
- prefill cache-slot borrowing;
- pinned staging ring;
- automatic placement cost model.

**DO NOT COPY DIRECTLY:**
- model-specific CUDA kernels;
- constants tuned for Qwen/RTX hardware;
- empirical placement coefficients.

## Next

After the controlled-spawn result and the planned research retrospective:

1. decide whether STRATA-H1..H5 deserve isolated finite-ram-lab experiments;
2. identify which belong to the core memory model versus an AI-worker application layer;
3. pin any reproduction to exact Strata commit `3ce2523c...` or newer explicitly reviewed commit.
