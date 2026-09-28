# Naive-N0.5-Flash intake for finite-ram-lab

> **Status:** SOURCE INTAKE / MECHANISM-TRANSFER CANDIDATE
> **Date:** 2026-09-28
> **Decision authority:** none; this document records research input only.

## Sources

- https://github.com/NaiveAI-Labs/Naive-N0.5-Flash
- https://huggingface.co/NaiveAI/Naive-N0.5-Flash
- https://naive.ai/en/research/

## Observed mechanisms

Naive-N0.5-Flash is a 309B MoE model with 15.5B active parameters and a native 1M-token context. Its attention stack uses 39 sliding-window-attention layers and 9 DeepSeek Sparse Attention layers. SWA uses a 128-token window. DSA indexes the full history but selects top-2,048 tokens for backbone attention. The published implementation retains the full KV cache while reducing attention computation and memory access.

The public configuration and model code expose:

- `sliding_window=128`;
- `index_top_k=2048`;
- GQA with four KV groups on DSA;
- DynamicCache-based KV retention;
- FP8 indexer activations;
- sparse selection before backbone attention.

The research write-up also describes fine-grained operator-output offload and distinguishes data worth retaining from bulk state that may be released or reconstructed.

## Transfer boundary

This source does **not** establish that POSIX_FADV_DONTNEED is beneficial for finite-ram-lab workloads.

Classification:

- evidence transfer: NO;
- mechanism transfer: YES;
- measurement-design transfer: STRONG YES.

GPU/HBM results are not Linux page-cache evidence.

## Atomized finite-ram implications

1. **Reuse horizon matters.**
   Release policy should eventually be tested against semantic reuse distance, not byte cadence alone.

2. **Retention and access are different costs.**
   A dataset may remain retained while memory traffic is reduced by sparse access. Future measurements should distinguish resident bytes from bytes touched/moved.

3. **Metadata can outlive bulk data.**
   Small decision/reconstruction metadata may deserve retention even when large reconstructible payloads are releasable.

4. **Candidate lifecycle classes.**
   A future study may refine HOT/COLD into HOT / REUSABLE / RECONSTRUCTIBLE / DEAD, but this is only a proposal.

5. **End-to-end cost dominates isolated microbenchmarks.**
   Memory saving, pressure avoidance, traffic, refault/reconstruction cost, and throughput should remain separately reported.

## Proposed follow-up, not authorized execution

After STRATA-005 completes, consider a STRATA-006 design:

**Release Cadence x Semantic Reuse Distance**

Candidate workload classes:

- one-shot / DEAD after scan;
- short-distance reuse;
- long-distance reuse;
- reconstructible bulk with retained metadata.

Candidate additional metrics include refault counters, I/O bytes, reconstruction latency, memory.current, pressure events, and end-to-end throughput.

## Frozen-current-study rule

Do not modify STRATA-005 arms, MemoryHigh levels, Recorder density, workload shape, or acceptance criteria based on this intake. New ideas enter only through a later explicit study design.
