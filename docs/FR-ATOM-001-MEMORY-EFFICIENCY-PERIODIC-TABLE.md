# FR-ATOM-001 — Memory Efficiency Periodic Table

Status: **SOURCE-GROUNDED ATOMIC INVENTORY**

Parent: **FR-GFX-007**

## Answer to "did we already do all quantization?"

No.

Finite RAM Lab already has a useful **foundational quantization taxonomy**:

- AWQ — weight quantization method;
- GPTQ — weight quantization method;
- NF4 — numeric representation;
- GGUF — container / tensor metadata format, **not** a quantizer;
- BitNet b1.58 — native model/architecture encoding, not an emergency runtime
  demotion of arbitrary models.

FP8 and NVFP4 also appear in source-grounded workload lanes.

But the lab has **not exhausted the quantization space**.

The largest missing quantization atoms are now:

1. activation quantization;
2. KV-cache quantization;
3. additive / codebook extreme quantization;
4. outlier-aware sparse high-precision escape;
5. dynamic mixed precision;
6. double quantization of scales/metadata.

Pinned new relatives:

- SmoothQuant — W8A8 activation/weight PTQ;
- KIVI — asymmetric 2-bit KV quantization;
- AQLM — additive codebook compression in the 2–3 bit regime;
- QuIP# — incoherence processing + lattice codebooks;
- SpQR — low-bit bulk weights plus sparse high-precision outliers.

The important conclusion is that **another weight-only quantizer is no longer
the highest-leverage missing atom**.

## The atomic memory equation

A useful first-order accounting model is:

[
M_{peak}
approx
sum_i
S_i Q_i R_i D_i C_i
+
F+P+X+Z_{meta}+O.
]

Where:

- (S): semantic obligation — how much information must survive;
- (Q): representation density — bytes per surviving unit;
- (R): resident fraction — how much of the representation must be in RAM now;
- (D): duplication factor — number of equivalent physical copies;
- (C): overlap/concurrency — how many temporary states coexist;
- (F): allocator / fragmentation / alignment slack;
- (P): page-cache / backing-IO footprint;
- (X): transfer / staging buffers;
- (Z_{meta}): compression / quantization metadata and workspaces;
- (O): observation/control overhead.

This is an accounting abstraction, not a claim that the terms are independent.

Its value is that every memory optimization must attack at least one term.

## Atom 1 — Semantic obligation

Question:

> Does this information need to exist at all?

Examples already studied:

- semantic context selection;
- KV/prefix dropping;
- sparse MoE activation;
- semantic OOM priorities.

This is stronger than compression because deleted/reconstructible information
can approach zero resident bytes.

Coverage: **strong**.

## Atom 2 — Representation density

Question:

> If it must exist, how many bytes encode it?

Existing:

- AWQ;
- GPTQ;
- NF4;
- BitNet;
- FP8/NVFP4 relatives.

Missing:

- SmoothQuant-style activation quantization;
- KIVI-style KV quantization;
- AQLM / QuIP# codebooks;
- SpQR-style outlier escape;
- dynamic precision by state/layer/token;
- quantized scales / metadata.

Coverage: **partial**.

## Atom 3 — Residency fraction

Question:

> Must the full representation be resident simultaneously?

Existing work is unusually strong here:

- streamed CRT folding;
- lane-concurrency sweeps;
- SSD tiers;
- expert caches;
- out-of-core model shards;
- cloud cold tier;
- graphics residency tiers.

Coverage: **strong**.

## Atom 4 — Duplication factor

Question:

> Why does the same immutable information exist more than once?

This is now the **largest obvious hole**.

Examples:

- multiple Python/model workers each loading identical weights;
- duplicated lookup tables;
- duplicated prefix/KV blocks;
- replicated host expert arenas;
- copied staging buffers.

Relevant mechanisms:

- shared file-backed mmap;
- copy-on-write;
- shared arenas;
- KSM for selected anonymous mergeable pages;
- prefix/KV sharing.

Linux KSM can merge identical anonymous pages into write-protected shared
pages, but the scan itself consumes CPU and only advised regions should be
considered.

Coverage: **gap**.

### Why this can dominate quantization

Suppose eight workers each privately hold a 4-bit 1 GiB-equivalent state:

[
8	imes0.25=2.0
]

full-precision-equivalent GiB of physical copies.

If instead one shared FP16 representation existed:

[
1	imes1.0=1.0.
]

In that simple geometry:

**sharing beats 4-bit quantization despite using a denser representation.**

Of course real compute/latency semantics may reverse the decision.

The point is:

[
oxed{
Q 	ext{ cannot be optimized without } D
}
]

## Atom 5 — Overlap / concurrency

Question:

> Which intermediate states coexist at peak?

Existing work:

- all-resident vs streamed exact CRT;
- residue-lane concurrency;
- demand folding;
- prefetch/speculation controls.

Missing:

- general rematerialization;
- activation lifetime scheduling;
- checkpointing.

Coverage: **strong core, rematerialization gap**.

## Atom 6 — Allocator / fragmentation

Question:

> How much RAM exists but cannot be usefully packed?

This is almost untouched.

PagedAttention is important because KV memory can be wasted by fragmentation
and duplicated blocks even when the numeric representation is unchanged.

vLLM's PagedAttention work explicitly targets near-zero KV waste and sharing
within/across requests.

A distinct relative, vAttention, attacks physical fragmentation while
preserving virtual contiguity.

This atom is independent of quantization.

Coverage: **gap**.

## Atom 7 — Page cache / IO path

Question:

> Did bytes supposedly "offloaded to SSD" silently return to RAM through the
> page cache or staging?

Existing Strata intake already exposed this failure domain.

Linux also provides reclaim/advice operations such as MADV_COLD and
MADV_PAGEOUT; process_madvise can apply advice to ranges.

Missing physical comparisons:

- mmap vs pread / unbuffered path;
- page-cache pollution;
- readahead;
- semantic cold-range advice.

Coverage: **partial**.

## Atom 8 — Transfer / staging

Question:

> Did moving memory require another copy?

Examples:

- host staging buffers;
- pinned buffers;
- double buffering;
- RAM→VRAM transfer queues.

The lab understands this concept through Strata/GTT work but has not isolated
the physical copy tax.

Coverage: **partial**.

## Atom 9 — Generic compression

Question:

> Can opaque bytes be compressed without understanding model semantics?

Existing:

- compressed-RAM tier;
- zram/zswap source intake.

Missing:

- codec choice;
- compression-ratio distribution;
- CPU cost;
- decompression tail;
- hot/cold compressibility classifier.

Coverage: **partial**.

## Atom 10 — Rematerialization / rebuild

Question:

> Is storing this cheaper than rebuilding it?

The classical activation-checkpointing result demonstrates the general
compute-for-memory trade.

Finite RAM already has drop/rebuild and streamed reconstruction ideas, but the
atom is not yet a first-class controller axis.

Coverage: **partial**.

## Atom 11 — Demand

Question:

> Why admit this much work simultaneously?

Demand folding is already a strong Finite RAM component.

Coverage: **strong**.

## Atom 12 — Topology

Question:

> Is one byte in this tier actually equivalent to one byte in another tier?

Existing:

- VRAM/GTT/RAM coupling;
- UMA;
- multi-GPU derivatives;
- SSD/cloud deadlines.

Missing:

- NUMA;
- CXL / memory expanders;
- explicit remote-memory tail models.

Coverage: **partial**.

## Atom 13 — Observation

Question:

> How much resource does the controller itself consume?

The FR-GFX chain now gives this atom unusually strong treatment.

Coverage: **strong**.

## Quantization status matrix

| Technique / class | Current Finite RAM state |
|---|---|
| AWQ | synthetic graph |
| GPTQ | synthetic graph |
| NF4 | numeric representation in graph |
| GGUF | container axis |
| BitNet b1.58 | native architecture class |
| FP8 | source-grounded partial |
| NVFP4 | source-grounded partial |
| SmoothQuant / W8A8 | **gap** |
| KIVI / KV quantization | **gap** |
| AQLM | **gap** |
| QuIP# | **gap** |
| SpQR | **gap** |
| dynamic mixed precision | **gap** |
| double-quantized metadata | **gap** |

## New research priority

The next experiment should **not** simply add another weight-only quantizer.

Priority:

1. **FR-SHARE-001 — duplication tax**
2. **FR-ALLOC-001 — fragmentation / paging**
3. **FR-QUANT-002 — activation + KV + extreme/mixed quantization**
4. **FR-REMAT-001 — recompute vs retain**
5. **FR-IO-001 — page-cache / direct IO**
6. **FR-COMP-001 — compression codec surface**
7. **FR-TOPO-001 — NUMA/CXL/remote topology**

## Strongest new hypothesis

The lab began with:

[
	ext{RAM problem} approx 	ext{too many bytes}.
]

The atomic view suggests a better statement:

[
oxed{
	ext{RAM pressure}
=
	ext{information}
	imes
	ext{representation}
	imes
	ext{residency}
	imes
	ext{duplication}
	imes
	ext{overlap}
+
	ext{allocation/IO/control taxes}.
}
]

Therefore no single compression algorithm can be globally optimal.

The correct Finite RAM controller chooses which **term** to attack for the
current failure domain.

## Claim ceiling

**SOURCE_GROUNDED_ATOMIC_INVENTORY_AND_RESEARCH_PRIORITIZATION_ONLY**
