# B432 — Strata Physical Frontier v0.1

Status: **source-backed static/structural model**. No physical benchmark ran.

Upstream pin:

- Niko1221/Strata
- commit 9259cad4cfa3543cd3b8decab5962672b968c649
- setup.py currently requires engine >= 0.1.31

## 1. Why Strata is the complementary test

Ozaki/GEMMul8 and FlashAttention mainly test logical-frontier rewriting: an intermediate can be replaced by a smaller future-sufficient state.

Strata attacks a different problem:

> the semantic state often remains required, but its representation, copy count, memory tier, ownership, and resident lifetime change.

This makes it a direct test of the **physical frontier** side of Live-State Frontier.

## 2. Source-backed KV representation

The current source describes QSA KV state with these storage footprints per cell:

- FP16: 2,048 bytes
- INT8: 1,056 bytes
- Q4_0: 576 bytes
- hybrid K8V4: 816 bytes

These are representation transformations.

### INT8 / Q4 streaming

With KV streaming enabled:

- the authoritative encoded KV lives in host memory;
- only a resident subset/window lives in VRAM;
- the page map resolves logical blocks to resident GPU slots;
- the encoded values themselves are unchanged by the move.

Therefore:

- INT8/Q4 quantization -> COMPRESS
- host/VRAM split -> MOVE

These are distinct transformations.

K8V4 is explicitly rejected with KV streaming in the current source, so B432 fails closed on that combination.

## 3. Static KV example

For a structural pool-only example:

- mode = INT8
- 12 QSA layers
- max_cells = 131,072
- resident_cells = 32,768

the source-backed per-cell storage formula gives:

- full encoded KV if entirely resident in VRAM:
  1,660,944,384 bytes = 1.546875 GiB
- GPU resident subset:
  415,236,096 bytes = 0.38671875 GiB
- host authoritative encoded copy:
  1,660,944,384 bytes
- VRAM avoided relative to full residency:
  1,245,708,288 bytes = 1.16015625 GiB

This is not total session memory. It excludes page maps, pooled index state, recurrence state, scratch, runtime allocations, and other engine structures.

The source docs report larger aggregate RAM-per-token numbers because the complete runtime state is broader than this isolated K/V pool formula.

## 4. Expert state: canonical information, several residency policies

The expert model separates semantic expert weights from physical copies.

### Normal resident mode

- large expert arena in host RAM;
- selected hot experts copied into the GPU expert cache.

This is:

- one logical expert set;
- host canonical physical state;
- GPU subset cache.

### mmap low-RAM mode

The expert file is mapped rather than copied wholesale into a pinned RAM arena.

Important rule:

> mapped file size is not resident RAM size.

The OS page cache may hold some mapped pages and reclaim them later.

Therefore B432 does **not** add the whole mapped file size to the RAM frontier.

Page-cache residency must be observed as a separate runtime quantity.

### resident low-RAM complement

The current source supports copying exactly the complement of the static GPU cache into RAM when it fits.

Conceptually:

logical experts
=
GPU resident subset
+
RAM complement.

There is no reason to keep a second full RAM copy merely because part of the state is also in VRAM.

This is both placement and duplicate avoidance.

### budgeted low-RAM

With a RAM budget:

logical experts
=
GPU subset
+
RAM-ranked subset
+
file-backed remainder.

Again the file-backed remainder is backing state, not automatically resident RAM.

## 5. Prompt cache lending

The single-GPU prompt path can borrow expert-cache slots for prompt buffers and refill those experts afterward.

This is important because it is not ordinary allocation growth.

Steady phase:

expert cache occupies region C.

Prompt phase:

part B of C is temporarily repurposed as prompt scratch.

After prompt:

the borrowed region is refilled with experts.

Therefore if prompt scratch fits within the borrowed region:

peak allocation for that region does not increase.

What changes is:

- phase-local expert capacity;
- refill traffic;
- temporary cache hit opportunity.

A public 2026-09-30 RTX 5090 log reports:

- expert cache: 23.44 GiB
- prompt path borrows 3,421 slots
- borrowed region: 4.62 GiB

Those are rounded runtime observations from that configuration, not universal constants.

## 6. Multi-GPU session ownership partition

The current source contains an important optimization beyond simple sharing.

Older layer-split behavior allocated whole-model-sized session state on each stage.

The current SessionState has:

- layer_lo / layer_hi
- qsa_ord0 / qsa_alloc
- gdn_ord0 / gdn_alloc

and the source explicitly describes the layer-range carve:

> a split stage owns only the QSA/GDN running state for the layer range it executes, apart from a required primary QSA state for model-level uses.

Conversation snapshots also save/restore only the state owned by that carve.

This is **OWNERSHIP PARTITION**:

semantic model state is partitioned according to the consumer that can actually update/use it.

It avoids physical duplication without changing model semantics.

The existing transformation vocabulary can represent this as a combination of:

- SHARE / de-duplicate ownership;
- REORDER / stage-local scheduling.

But the concept deserves an explicit property in future compiler inputs: **owner set**.

## 7. Shared host expert arena

For layer-split multi-GPU serving the docs describe:

- dense/session/cache state per device as appropriate;
- one host expert arena shared by all cards.

A separate community experiment also demonstrates request-level independent GPU lanes sharing a MAP_SHARED expert arena while keeping GPU/session failure domains lane-local.

This is a canonical SHARE pattern:

N logical consumers
do not require
N physical host copies
when the weights are immutable and shareable.

## 8. Idle unload

The server exposes an idle-unload policy:

- after a configured idle interval, unload the model;
- the next request reloads it.

This does not reduce loaded peak memory.

It reduces **byte-seconds over wall time**.

If a resident set M is needed for only active time A inside horizon H:

always-loaded exposure = M * H

idle-unloaded exposure = M * A.

So lifetime control primarily improves A, the byte-seconds objective, rather than P, the loaded peak.

## 9. B428 compiler schema failure

This was the most important result of B432.

B428 has one scalar:

physical_bytes.

That is insufficient for Strata.

Example:

- VRAM = 8 GiB
- RAM = 20 GiB

A flat compiler sees:

28 GiB physical.

But feasibility is actually constrained independently:

8 GiB <= C_VRAM

20 GiB <= C_RAM.

The two capacities are not interchangeable.

Therefore the B428 semantic taxonomy survives, but its physical compiler representation needs a tier dimension.

## 10. Tiered Frontier compiler

B432 adds:

- src/finite_ram_lab/tiered_frontier.py

Each resident state has:

- logical_bytes
- resident_bytes
- tier
- live interval.

The compiler emits:

- logical peak;
- total resident peak;
- peak bytes per tier;
- byte-seconds per tier;
- interval records;
- per-tier capacity ratios.

Minimum useful tiers today:

- VRAM
- RAM

Backing storage is not treated as resident memory.

A later extension can distinguish:

- pinned RAM
- pageable RAM
- OS page cache
- SSD backing

when those distinctions materially change cost.

## 11. Flat-to-tiered adapter rule

B432 also corrects an accounting trap.

If one semantic KV object has:

- authoritative host copy;
- resident GPU window,

its logical bytes must be counted **once**.

The host/GPU copies are physical replicas/placements only.

Likewise an expert model split across GPU, RAM, and file backing is one logical expert set.

The adapter therefore emits:

- one semantic logical state;
- zero-logical-byte physical tier records.

This prevents logical-state double counting.

## 12. Validation

Frozen software:

- src/finite_ram_lab/strata_physical_frontier.py
- src/finite_ram_lab/tiered_frontier.py
- tests/test_strata_physical_frontier.py
- analysis/inputs/B432-STRATA-PHYSICAL-FRONTIER-v0.1.json

Authoring validation:

- fixed source-backed KV arithmetic: PASS
- unsupported K8V4 + streaming gate: PASS
- complement accounting: PASS
- prompt cache lending invariant: PASS
- ownership partition arithmetic: PASS
- idle-unload byte-seconds arithmetic: PASS
- semantic-state single-count adapter: PASS
- tier capacity separation: PASS
- 20,000 deterministic randomized tier traces: PASS

Claim ceiling:

SOURCE_BACKED_STATIC_AND_STRUCTURAL_MODEL.

No Strata benchmark was executed by Finite RAM Lab in this bounce.

## 13. Cross-domain status after B432

The model has now survived three qualitatively different cases.

### Numerical decomposition

Ozaki / GEMMul8:

- representation;
- hierarchical reduction;
- workspace blocking;
- axis temporalization.

### Exact attention

FlashAttention:

- future-sufficient running state;
- semantic liveness;
- tile-axis temporalization.

### LLM residency manager

Strata:

- compression;
- tier placement;
- sharing;
- ownership partition;
- phase-local borrowing;
- lifetime contraction;
- mapped backing.

The semantic transformation set did not need a new category.

The physical compiler did need a tier dimension.

## 14. B433 candidate

Freeze **Live-State Frontier Taxonomy v0.2** with two explicit planes:

### Semantic plane

- logical state
- future obligation
- sufficient summary
- regenerability
- ownership

### Physical plane

- representation
- replica count
- resident tier
- backing tier
- live interval
- phase
- capacity

Then define a controller order:

1. shorten semantic liveness;
2. remove duplicate ownership;
3. choose representation;
4. schedule/temporalize legal axes;
5. assign tiers;
6. borrow idle capacity across phases;
7. unload across idle wall time.

Only after this should a cost optimizer trade traffic/compute/latency/error.
