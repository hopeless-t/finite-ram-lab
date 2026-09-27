# LLM Memory Semantics Intake v1

> **Status:** CONCEPTUAL INTAKE / NO EXECUTION AUTHORITY
> **Source:** https://note.com/npaka/n/n0ee92a316be3
> **Source title:** ローカルLLMのためのメモリ基礎知識
> **Published:** 2026-09-27

## Why this source is useful

The source is introductory rather than a new memory-management algorithm.

Its value to Finite RAM Lab is the explicit separation of:

- CPU / GPU compute;
- RAM / VRAM capacity;
- unified/shared memory;
- model weights;
- KV cache;
- inference workspace;
- capacity reduction techniques;
- memory bandwidth.

That vocabulary helps prevent one generic "memory usage" bucket from hiding semantically different lifetimes and reuse patterns.

## Finite RAM semantic classes for local LLMs

### PERSISTENT_HOT — model weights

Typical properties:

- large;
- long-lived for the loaded model;
- repeatedly consumed during generation;
- often bandwidth-critical;
- may live in VRAM, RAM, unified memory, or a split/tiered arrangement.

Default policy:

- **do not treat as COLD merely because the backing file was loaded once**;
- do not apply streaming DONTNEED to pages that the active inference engine expects to reuse.

The distinction between backing-file I/O and active resident model state must be explicit.

### SESSION_HOT — KV cache

Typical properties:

- lifetime tied to an active conversation/request/session;
- grows with context length;
- repeatedly reused during generation;
- capacity sensitive;
- potentially quantizable or evictable only through inference-engine-aware policy.

Default policy:

- application/inference-engine owned;
- generic OS-level COLD hints are inappropriate while the session is active.

### PHASE_HOT — inference workspace / temporary buffers

Typical properties:

- temporary;
- may be large;
- hot only during a kernel/phase/batch;
- release point can be semantically known.

Default policy:

- explicit phase-end release is valuable;
- allocator/arena reuse may be better than OS advice;
- distinguish reusable workspace from leaked/stale capacity.

### STREAM_COLD — one-shot load/staging data

Examples:

- file ranges consumed only to construct another resident representation;
- model conversion/loading staging buffers;
- one-pass dataset/model-shard scans;
- build/index/backup inputs that are not expected to be reused soon.

Default policy candidate:

- ordinary buffered read;
- after a completed aligned range becomes semantically dead, apply bounded DONTNEED;
- this is the direct STRATA-002 candidate.

### REUSABLE_WARM — uncertain-near-future data

Typical properties:

- may be revisited;
- reuse probability is nonzero but not session-critical;
- page cache may be useful.

Default policy:

- leave under normal kernel page-cache policy unless evidence supports a stronger hint.

## Capacity and bandwidth are separate axes

Finite RAM Lab must not optimize capacity while silently destroying throughput.

For local LLM work, report both:

### Capacity / pressure

- resident footprint;
- available/recovered headroom;
- file-cache retention;
- swap/reclaim/pressure events;
- RAM/VRAM placement.

### Bandwidth / throughput

- scan/load throughput;
- inference tokens/s;
- time-to-first-token;
- per-token steady-state latency;
- host↔device transfer where relevant.

This extends STRATA-002's existing memory-efficiency bundle rather than replacing it.

## Important DONTNEED safety rule

The STRATA-002 result does **not** imply:

"apply DONTNEED to all LLM model files."

The optimization only makes sense when a consumed file range is semantically one-shot/COLD.

If mmap-backed model weights are actively reused through the page cache, dropping them can increase refault/I/O and hurt inference.

Therefore any future helper must require an explicit or strongly evidenced semantic contract before advising DONTNEED.

## Unified-memory note

On systems where CPU/GPU share one physical memory pool, the distinction between RAM and VRAM capacity is less physically separate, but semantic classes still matter.

The planner should reason about:

- shared total capacity;
- reserved OS/application capacity;
- active model state;
- KV growth;
- workspace peaks;
- bandwidth contention.

Do not equate total unified memory with fully available model capacity.

## Local dogfood implications

When the real personal-PC path becomes authorized, first dogfood should not start from an LLM engine mutation.

Safer sequence:

1. reproduce STRATA-002 on a bounded synthetic one-shot stream;
2. measure the same RFR/RMH/CCRF/PES/SCR metrics locally;
3. only then choose one real workload whose STREAM_COLD range is clear;
4. preserve PERSISTENT_HOT / SESSION_HOT regions untouched;
5. add LLM-specific throughput metrics only when moving into actual inference.

## Research branches enabled by this intake

### LLM-RESIDENCY-001

Map a real inference engine's allocations/backing files into:

- PERSISTENT_HOT;
- SESSION_HOT;
- PHASE_HOT;
- STREAM_COLD;
- REUSABLE_WARM.

Read-only instrumentation first.

### LLM-BANDWIDTH-001

Test whether memory-footprint savings alter:

- model load time;
- token throughput;
- TTFT;
- steady-state latency.

Only after a specific COLD range is identified.

### UNIFIED-MEMORY-001

Future branch for systems with a shared CPU/GPU memory pool.

Not a current priority for the user's discrete-memory Lubuntu path unless hardware changes.

## Decision

**ABSORB taxonomy and measurement framing.**

Do not treat the article as evidence for DONTNEED itself.

Do not open a new physical experiment solely from this source.

Use it to improve semantic classification and local-LLM external-validity design.

## Authority boundary

Conceptual research only.
