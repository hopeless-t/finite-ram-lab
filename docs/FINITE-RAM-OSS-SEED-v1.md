# Finite RAM OSS Seed v1

> **Status:** PRODUCT SEED / DO NOT EXTRACT YET
> **Origin:** STRATA-001 / STRATA-002 / LOCAL-VALIDITY-001
> **Working name:** `finite-ram-helper` (not final)

## Product thesis

A small application-facing helper should let software declare:

> "this file range has been consumed and is semantically COLD / one-shot"

and translate that declaration into a bounded operating-system memory hint.

The first validated candidate mechanism is Linux:

`POSIX_FADV_DONTNEED`

applied incrementally to already-consumed aligned ranges of a normal buffered stream.

The helper should preserve ordinary buffered-I/O semantics and leave global reclaim policy to the kernel.

## Why this is worth extracting

STRATA-002 hosted pilot observed, for the tested workload:

- paired median resident-footprint reduction: ~52.13%;
- median saved footprint: ~82.98 MiB;
- recovered MemoryHigh headroom: ~83.46 MiB;
- COLD-file residency: ~86.5% -> 0%;
- MemoryHigh-event suppression: 100% in 8/8 blocks;
- pressure footprint approximately matching the O_DIRECT reference.

NOREUSE did not materially reduce the immediate footprint in the same pilot.

The mechanism is promising enough for productization research, but not yet proven across real personal-PC workloads.

## Product shape

### Core abstraction

A minimal semantic API such as:

`mark_consumed_cold(file, offset, length)`

or a streaming wrapper that automatically releases completed ranges.

The public API should speak in semantic terms.

Linux syscall details remain behind the adapter.

### Candidate surfaces

Phase 1:

- library/helper API;
- bounded CLI demonstrator;
- metrics/report mode.

Potential later surfaces:

- Python package;
- Rust crate;
- C-compatible core for embedding;
- adapters for data/model/build pipelines.

No language commitment is frozen yet.

## Required semantic classes

The helper must never treat all memory/file traffic equally.

At minimum:

- `PERSISTENT_HOT`
- `SESSION_HOT`
- `PHASE_HOT`
- `STREAM_COLD`
- `REUSABLE_WARM`

Only explicit `STREAM_COLD` ranges are eligible for automatic DONTNEED in v1.

## Hard non-goals

The OSS must **not** become:

- a global `drop_caches` button;
- a generic "RAM cleaner";
- an automatic model-weight cache dropper;
- a KV-cache manager;
- a kernel/sysctl tuner;
- an opaque background daemon that guesses user intent;
- a system-wide O_DIRECT switch;
- a benchmark trick that optimizes RAM by hiding throughput regressions.

## Safety invariants

1. **Semantic opt-in**
   - no COLD hint without explicit caller contract.

2. **Bounded range**
   - advice applies only to already-consumed declared ranges.

3. **No hidden fallback claims**
   - advice unsupported/failure must be observable.

4. **No data mutation**
   - memory advice must not modify file contents.

5. **No global cache mutation**
   - never write global cache-dropping controls.

6. **Capacity + bandwidth accounting**
   - report memory savings and time/throughput cost separately.

7. **Fail open for correctness, fail explicit for optimization**
   - inability to apply an advisory optimization must not corrupt application behavior;
   - it must not be silently reported as successful optimization.

## Standard metrics

Every dogfood/benchmark should report:

- RFR — Resident Footprint Reduction;
- RMH / NRH — Recovered Memory Headroom;
- CCRF — Cold Cache Retention Fraction;
- PES — Pressure Event Suppression;
- SCR — Scan-Time Cost Ratio;
- raw MiB/s.

When a direct-I/O reference exists:

- CSAF — Cold-Stream Amplification Factor.

For LLM inference integration later:

- model load time;
- TTFT;
- tokens/s;
- context length;
- KV-cache size/format.

## Extraction gates

### G0 — hosted mechanism

**PASS**

STRATA-002 demonstrates a strong hosted pressure-footprint mechanism.

### G1 — local synthetic external validity

**PENDING**

LOCAL-VALIDITY-001 must reproduce a meaningful pressure benefit on the target personal Linux machine using a generated disposable file.

No real workload yet.

### G2 — one real STREAM_COLD dogfood

**PENDING**

Use one workload whose one-shot semantics are clear.

Examples:

- checksum/verification pass;
- conversion staging;
- build-artifact scan;
- indexing input;
- disposable dataset pass.

### G3 — portability boundary

**PENDING**

Characterize at least:

- kernel/version assumptions;
- filesystem behavior;
- advice support/failure behavior;
- alignment/granularity;
- effect on NVMe/SATA where relevant.

### G4 — stable cost envelope

**PENDING**

Memory benefit must coexist with an acceptable throughput/latency envelope on fixed hardware.

### G5 — OSS extraction

Only after G1–G4 provide enough evidence.

At G5:

- create standalone repo;
- define supported Linux baseline;
- publish minimal API;
- include evidence-backed examples;
- ship a benchmark command reproducing the metric bundle;
- document explicit non-goals.

## Release posture

Do not market this as "make your PC use 52% less RAM."

The evidence-backed claim format should look like:

> For bounded one-shot file streams, this helper can advise Linux to release already-consumed file-cache ranges. In our tested workloads it materially reduced retained file-cache pressure; actual savings depend on workload, kernel, filesystem, and reuse semantics.

## Relationship to Finite RAM Lab

Finite RAM Lab remains the research/evidence repository.

The future OSS should be an extracted implementation artifact, not the place where hypotheses are invented.

Research first; product second.

## Relationship to MVCA

Future local dogfood should use the existing secure path only under explicit finite-ram-specific admission/lease:

`Web ChatGPT → Secure MCP Tunnel → MVCA → bounded local tool`

Transport availability never creates execution authority.

## Decision

Preserve this product seed now.

Do not create the standalone OSS repository until local external validity and at least one real dogfood workload justify extraction.
