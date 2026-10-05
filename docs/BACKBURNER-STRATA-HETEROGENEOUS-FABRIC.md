# Backburner × Strata: Heterogeneous Spill Fabric

**Status:** research intake / hypothesis only  
**Date:** 2026-10-05  
**Authority:** no production adoption implied

## Why this belongs in Finite RAM Lab

Finite RAM Lab already has `STRATA-001`, motivated by Strata's explicit VRAM/RAM/SSD tiering and its separation of semantically HOT and COLD data.

Backburner adds a new systems dimension: a second physical device can contribute both **memory capacity** and **compute** while the primary machine continues to own the logical inference request.

Upstream references:

- Strata: https://github.com/Niko1221/Strata
- Strata v0.1.39: https://github.com/Niko1221/Strata/releases/tag/v0.1.39
- Backburner: https://github.com/StayLameBro/backburner
- PC Watch summary: https://pc.watch.impress.co.jp/docs/news/2145651.html

## Atomic decomposition

### Strata

Strata demonstrates an application-controlled hierarchy across:

- GPU VRAM for hot/shared computation and frequently used experts;
- host RAM for the complete expert population;
- CPU execution for experts not resident on the GPU;
- SSD for lookup-oriented model state;
- multi-GPU helper paths;
- dynamic expert residency based on observed use.

The v0.1.39 release additionally reports long-prompt improvements, multi-GPU overlap, remote-expert optimization, concurrency controls, and expanded support for older hardware.

### Backburner

Backburner demonstrates a different cut through the same general problem:

- up to a threshold, the host runs early layers while an iPhone runs later layers;
- beyond the host context threshold, the phone changes role and stores old KV pages;
- the phone computes attention over those remote old keys;
- the host merges partial attention results with its local result;
- CPU, GPU, Neural Engine, SSD cache, and a remote phone are treated as one inference resource fabric;
- a second phone can share old KV pages;
- the system keeps logical inference ownership on the host while moving selected state and kernels elsewhere.

The notable property is **role switching by resource pressure** rather than a fixed device partition.

## Research hypothesis

> A finite-memory system can move its practical capacity boundary farther by jointly scheduling **residency and computation** across heterogeneous local/remote resources, instead of treating RAM pressure as a memory-only problem.

This is broader than swap or storage offload.

A candidate resource graph is:

```text
logical inference state
       |
       +-- host RAM
       +-- accelerator VRAM
       +-- host CPU
       +-- local SSD
       +-- remote RAM
       +-- remote accelerator
       +-- remote CPU/NPU
```

The scheduling unit should not necessarily be "the process" or "the model". Candidate atomic units include:

- tensor;
- layer range;
- expert;
- KV page;
- attention partition;
- matrix rows/tiles;
- reconstructable cache state;
- immutable lookup tables.

## HSF-001 — Heterogeneous Spill Fabric

### Question

Under a fixed host-RAM limit, when is it beneficial to move a state+compute unit to another tier or device instead of reclaiming, recomputing, quantizing, or failing?

### Cost model

For candidate placement `p` of unit `u`:

```text
cost(u, p) =
    compute_time
  + transfer_time
  + memory_pressure_penalty
  + synchronization_penalty
  + reconstruction_cost
  + energy_cost
  + thermal_penalty
  + failure_risk
```

The first experiment should not optimize this scalar directly. Each term should be measured independently before any composite controller is trusted.

### Initial localhost PoC

Avoid hardware dependence first.

Run two local processes that emulate host and helper-device boundaries:

1. create a small deterministic attention/model workload;
2. split one resource unit across process A/B;
3. impose artificial link bandwidth/latency;
4. compare local-only versus remote-spill paths;
5. record bytes transferred, resident bytes, wall time, CPU time, and correctness;
6. inject helper loss mid-run;
7. verify that fallback does not duplicate logical work or silently corrupt state.

Candidate progression:

```text
localhost process split
    -> same-machine socket
    -> LAN helper
    -> USB-connected helper
    -> heterogeneous real devices
```

### Candidate variants

- **HSF-001A:** remote KV-page residency only;
- **HSF-001B:** remote KV + partial attention compute;
- **HSF-001C:** layer-tail pipeline;
- **HSF-001D:** dynamic role switching at a pressure threshold;
- **HSF-001E:** N-helper sharding of immutable old state;
- **HSF-001F:** recompute-vs-transfer-vs-retain decision boundary.

## Required validity checks

A benchmark PASS must require at least:

- bitwise or tolerance-bounded output contract;
- explicit host and helper resident-byte accounting;
- explicit transfer-byte accounting;
- synchronization/completion correctness;
- injected helper disconnect/restart path;
- no duplicate logical execution after ambiguous transport outcomes;
- pressure threshold recorded before and after intervention;
- independent local-only baseline.

## Relationship to STRATA-001

`STRATA-001` asks whether semantically COLD file data can avoid disturbing HOT anonymous memory.

`HSF-001` asks the next question:

> if local memory remains insufficient, can the system move selected **state together with the computation that consumes it** to another resource tier?

So the conceptual progression is:

```text
semantic residency
  -> local memory/storage tiering
  -> compute-aware tiering
  -> remote state+compute spill
  -> adaptive heterogeneous fabric
```

## Non-claims

This note does not claim that:

- Backburner is faster on arbitrary hardware;
- remote execution always beats recomputation or local quantization;
- phone offload is appropriate for Linux hosts;
- network/USB offload is universally beneficial;
- a single scalar scheduler objective is sufficient;
- HSF-001 has been implemented or validated.

The immediate value of Backburner and Strata is as inspectable prior art showing that **resource roles can be assigned by semantic state and changed with pressure**.